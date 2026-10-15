import os
import sys
import logging
from datetime import datetime
from typing import Tuple
import boto3
import pandas as pd
from snowflake.connector import connect
from snowflake.connector.errors import ProgrammingError
from config import Config
from schema_validator import SchemaValidator
from data_validator import DataValidator


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_s3_client():
    """Create S3 client from AWS credentials in environment."""
    return boto3.client("s3", region_name=os.getenv("AWS_REGION"))


def get_snowflake_connection():
    """Create Snowflake connection from environment configuration."""
    return connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        role=os.getenv("SNOWFLAKE_ROLE"),
    )


def read_csv_from_s3(s3_client, bucket: str, key: str) -> pd.DataFrame:
    """Read CSV from S3 into pandas DataFrame."""
    try:
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(obj["Body"], dtype_backend="numpy_nullable")
        logger.info(f"Read CSV from s3://{bucket}/{key}. Rows: {len(df)}, Columns: {len(df.columns)}")
        return df
    except Exception as e:
        logger.error(f"Failed to read CSV from s3://{bucket}/{key}: {e}")
        raise


def load_raw_to_snowflake(
    conn, df: pd.DataFrame, table_name: str, config: Config
) -> Tuple[int, int]:
    """Load validated DataFrame to Snowflake raw staging table. Returns (loaded_count, rejected_count)."""
    cursor = conn.cursor()
    loaded_count = 0
    rejected_count = 0

    try:
        # Truncate raw staging table to prepare for full load
        cursor.execute(f"TRUNCATE TABLE {table_name}")
        logger.info(f"Truncated {table_name}")

        # Convert DataFrame to list of tuples for batch insert
        rows = [
            tuple(None if pd.isna(v) else v for v in row)
            for row in df.itertuples(index=False, name=None)
        ]
        loaded_count = len(rows)

        # Use parameterized insert to prevent SQL injection
        columns = ",".join(df.columns)
        placeholders = ",".join(["?" for _ in df.columns])
        insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        cursor.executemany(insert_sql, rows)
        conn.commit()
        logger.info(f"Loaded {loaded_count} rows into {table_name}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to load data to {table_name}: {e}")
        rejected_count = loaded_count
        loaded_count = 0
        raise
    finally:
        cursor.close()

    return loaded_count, rejected_count


def quarantine_rejected_records(
    conn, rejected_df: pd.DataFrame, reason: str, config: Config
) -> None:
    """Write rejected records to quarantine table with reason."""
    if rejected_df.empty:
        return

    cursor = conn.cursor()
    try:
        quarantine_table = f"{config.SNOWFLAKE_SCHEMA}.{config.QUARANTINE_TABLE}"
        rejected_df["rejection_reason"] = reason
        rejected_df["rejected_at"] = datetime.utcnow().isoformat()
        rejected_df["source_file"] = config.S3_KEY

        rows = [
            tuple(None if pd.isna(v) else v for v in row)
            for row in rejected_df.itertuples(index=False, name=None)
        ]

        columns = ",".join(rejected_df.columns)
        placeholders = ",".join(["?" for _ in rejected_df.columns])
        insert_sql = f"INSERT INTO {quarantine_table} ({columns}) VALUES ({placeholders})"

        cursor.executemany(insert_sql, rows)
        conn.commit()
        logger.info(f"Quarantined {len(rejected_df)} rejected records")
    except Exception as e:
        logger.error(f"Failed to quarantine rejected records: {e}")
        conn.rollback()
    finally:
        cursor.close()


def execute_transformation_sql(conn, config: Config) -> None:
    """Execute transformation SQL to populate target table from raw staging."""
    cursor = conn.cursor()
    try:
        with open(config.TRANSFORMATION_SQL_PATH, "r") as f:
            sql = f.read()
        cursor.execute(sql)
        conn.commit()
        logger.info("Transformation SQL executed successfully")
    except ProgrammingError as e:
        logger.error(f"Transformation SQL failed: {e}")
        conn.rollback()
        raise
    except Exception as e:
        logger.error(f"Failed to execute transformation: {e}")
        raise
    finally:
        cursor.close()


def record_execution_metrics(
    conn,
    config: Config,
    status: str,
    loaded_count: int,
    rejected_count: int,
    error_message: str = None,
) -> None:
    """Record pipeline execution metrics for monitoring and reconciliation."""
    cursor = conn.cursor()
    try:
        metrics_table = f"{config.SNOWFLAKE_SCHEMA}.pipeline_execution_metrics"
        cursor.execute(
            f"""
            INSERT INTO {metrics_table}
            (pipeline_name, execution_date, status, records_loaded, records_rejected, error_message, executed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                config.PIPELINE_NAME,
                config.EXECUTION_DATE,
                status,
                loaded_count,
                rejected_count,
                error_message,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        logger.info(f"Recorded execution metrics: status={status}, loaded={loaded_count}, rejected={rejected_count}")
    except Exception as e:
        logger.warning(f"Failed to record execution metrics: {e}")
        conn.rollback()
    finally:
        cursor.close()


def run_pipeline() -> int:
    """Execute end-to-end ETL pipeline. Returns 0 on success, 1 on failure."""
    config = Config()
    s3_client = None
    conn = None
    loaded_count = 0
    rejected_count = 0
    error_message = None

    try:
        logger.info(f"Pipeline started: {config.PIPELINE_NAME}")
        s3_client = get_s3_client()
        conn = get_snowflake_connection()

        # Read CSV from S3
        raw_df = read_csv_from_s3(s3_client, config.S3_BUCKET, config.S3_KEY)

        # Validate schema
        validator = SchemaValidator(config.SCHEMA_PATH)
        valid_df, invalid_df = validator.validate(raw_df)

        if not invalid_df.empty:
            logger.warning(f"Schema validation failed for {len(invalid_df)} rows")
            quarantine_rejected_records(
                conn, invalid_df, "Schema validation failed", config
            )
            rejected_count += len(invalid_df)

        # Validate data quality
        if not valid_df.empty:
            data_validator = DataValidator()
            quality_df, quality_invalid_df = data_validator.validate(valid_df)

            if not quality_invalid_df.empty:
                logger.warning(f"Data quality validation failed for {len(quality_invalid_df)} rows")
                quarantine_rejected_records(
                    conn, quality_invalid_df, "Data quality validation failed", config
                )
                rejected_count += len(quality_invalid_df)

            # Load valid records to Snowflake raw staging
            if not quality_df.empty:
                loaded_count, _ = load_raw_to_snowflake(
                    conn, quality_df, f"{config.SNOWFLAKE_SCHEMA}.{config.RAW_TABLE}", config
                )

        # Execute transformation SQL
        if loaded_count > 0:
            execute_transformation_sql(conn, config)

        # Record success metrics
        record_execution_metrics(
            conn, config, "SUCCESS", loaded_count, rejected_count
        )
        logger.info(f"Pipeline completed successfully. Loaded: {loaded_count}, Rejected: {rejected_count}")
        return 0

    except Exception as e:
        error_message = str(e)
        logger.error(f"Pipeline failed with error: {error_message}", exc_info=True)
        record_execution_metrics(
            conn, config, "FAILED", loaded_count, rejected_count, error_message
        )
        return 1

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    sys.exit(run_pipeline())
