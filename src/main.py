#!/usr/bin/env python
import sys
import logging
import uuid
from datetime import datetime

from src.config import PipelineConfig
from src.s3_client import S3Client
from src.snowflake_client import SnowflakeClient
from src.csv_validator import CSVValidator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Expected CSV columns (inferred from common orders schema)
EXPECTED_COLUMNS = ["order_id", "customer_id", "order_date", "amount", "status"]


def main() -> int:
    """
    Main ETL pipeline:
    1. Find latest CSV in S3
    2. Validate and parse CSV
    3. Load valid records into Snowflake staging table
    4. Load malformed records into quarantine table
    5. Replace target table with valid records
    6. Record execution metadata
    """
    execution_id = str(uuid.uuid4())
    logger.info(f"Starting pipeline execution {execution_id}")

    try:
        # Load configuration
        config = PipelineConfig.from_env()
        logger.info(f"Configuration loaded for {config.s3.bucket}")

        # Initialize clients
        s3_client = S3Client(config.s3.bucket, config.s3.region)
        sf_client = SnowflakeClient(config.snowflake)
        sf_client.connect()

        # Find latest CSV in S3
        csv_key, last_modified = s3_client.find_latest_csv(config.s3.key_prefix)
        if not csv_key:
            logger.error("No CSV file found in S3")
            sf_client.record_execution(
                config.metadata_table,
                execution_id,
                "NOT_FOUND",
                0,
                0,
                "FAILED",
            )
            return 1

        logger.info(f"Found CSV: s3://{config.s3.bucket}/{csv_key}")

        # Download and parse CSV
        csv_bytes = s3_client.download_csv(csv_key)
        validator = CSVValidator(EXPECTED_COLUMNS)
        valid_df, malformed_records = validator.validate_and_parse(csv_bytes)

        if valid_df.empty:
            logger.error("No valid records found in CSV")
            sf_client.record_execution(
                config.metadata_table,
                execution_id,
                csv_key,
                0,
                len(malformed_records),
                "FAILED",
            )
            return 1

        # Truncate staging table and load valid records
        sf_client.truncate_table(config.staging_table)
        valid_records = valid_df.to_dict("records")
        sf_client.insert_records(config.staging_table, valid_records)

        # Load malformed records into quarantine
        if malformed_records:
            sf_client.truncate_table(config.quarantine_table)
            # Prepare malformed records with string representations
            malformed_for_insert = [
                {
                    "row_number": m["row_number"],
                    "raw_data": str(m["row_data"]),
                    "error_reason": m["error_reason"],
                }
                for m in malformed_records
            ]
            sf_client.insert_records(config.quarantine_table, malformed_for_insert)
            logger.info(f"Loaded {len(malformed_records)} malformed records to quarantine")

        # Replace target table with valid data from staging
        sf_client.truncate_table(config.target_table)
        sf_client.execute(
            f"INSERT INTO {config.target_table} SELECT * FROM {config.staging_table}"
        )
        logger.info(
            f"Loaded {len(valid_records)} records into {config.target_table}"
        )

        # Record successful execution
        sf_client.record_execution(
            config.metadata_table,
            execution_id,
            csv_key,
            len(valid_records),
            len(malformed_records),
            "SUCCESS",
        )

        # Mark file as processed in S3
        s3_client.record_processed_file(csv_key, execution_id)

        logger.info(
            f"Pipeline execution {execution_id} completed successfully. "
            f"Valid: {len(valid_records)}, Malformed: {len(malformed_records)}"
        )
        sf_client.disconnect()
        return 0

    except Exception as e:
        logger.error(f"Pipeline execution {execution_id} failed: {e}", exc_info=True)
        try:
            sf_client.record_execution(
                config.metadata_table,
                execution_id,
                csv_key if "csv_key" in locals() else "UNKNOWN",
                0,
                0,
                "FAILED",
            )
        except Exception as log_err:
            logger.error(f"Failed to record execution failure: {log_err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
