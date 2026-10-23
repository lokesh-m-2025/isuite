#!/usr/bin/env python3
"""
Daily Orders CSV to Snowflake ELT Pipeline.

Production-grade batch ETL that loads orders from CSV (S3/local),
validates, and transforms data in Snowflake.
"""

import logging
import sys
from datetime import datetime
from uuid import uuid4

from src.config import PipelineConfig
from src.ingestion import read_csv_from_source
from src.validation import validate_dataframe, check_duplicates
from src.snowflake_ops import (
    create_connection,
    create_staging_table,
    create_rejected_table,
    create_target_table,
    create_pipeline_log_table,
    insert_raw_records,
    insert_rejected_records,
    transform_raw_to_target,
    log_execution
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_pipeline() -> None:
    """Main pipeline execution."""
    execution_id = str(uuid4())
    start_time = datetime.utcnow()
    conn = None

    try:
        logger.info(f"Starting pipeline execution {execution_id}")

        # Load configuration
        config = PipelineConfig.from_env()
        logger.info(f"Configuration loaded: source={config.input_source}, file={config.csv_filename}")

        # Read CSV
        logger.info(f"Reading CSV from {config.input_source}{config.csv_filename}")
        df = read_csv_from_source(config.input_source, config.csv_filename)
        records_read = len(df)
        logger.info(f"Read {records_read} records from CSV")

        # Validate records
        logger.info("Validating records against schema")
        valid_records, validation_errors = validate_dataframe(df)
        logger.info(f"Validation complete: {len(valid_records)} valid, {len(validation_errors)} rejected")

        # Check for duplicates within batch
        logger.info("Checking for duplicate order_ids")
        valid_records, duplicate_errors = check_duplicates(valid_records)
        all_errors = validation_errors + duplicate_errors
        logger.info(f"After duplicate check: {len(valid_records)} valid, {len(all_errors)} total rejected")

        # Connect to Snowflake
        logger.info("Connecting to Snowflake")
        conn = create_connection(config.snowflake)

        # Ensure tables exist
        create_staging_table(conn)
        create_rejected_table(conn)
        create_target_table(conn)
        create_pipeline_log_table(conn)

        # Load valid records to staging
        if valid_records:
            logger.info(f"Loading {len(valid_records)} valid records to RAW_ORDERS")
            insert_raw_records(conn, valid_records)
        else:
            logger.warning("No valid records to load")

        # Load rejected records
        if all_errors:
            logger.info(f"Loading {len(all_errors)} rejected records to REJECTED_ORDERS")
            insert_rejected_records(conn, all_errors)

        # Transform to target
        logger.info("Transforming data from staging to ORDERS table")
        transformed_count = transform_raw_to_target(conn)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Log execution success
        log_execution(
            conn,
            execution_id,
            "daily_orders_pipeline",
            "SUCCESS",
            records_read,
            len(valid_records),
            len(all_errors),
            start_time,
            end_time
        )

        logger.info(f"Pipeline completed successfully in {duration:.2f}s")
        logger.info(f"Summary: read={records_read}, valid={len(valid_records)}, "
                    f"rejected={len(all_errors)}, transformed={transformed_count}")

    except Exception as e:
        end_time = datetime.utcnow()
        error_msg = str(e)
        logger.error(f"Pipeline failed: {error_msg}")

        # Log execution failure
        try:
            if conn:
                log_execution(
                    conn,
                    execution_id,
                    "daily_orders_pipeline",
                    "FAILED",
                    0,
                    0,
                    0,
                    start_time,
                    end_time,
                    error_msg[:2048]
                )
        except Exception as log_err:
            logger.error(f"Failed to log error: {str(log_err)}")

        sys.exit(1)

    finally:
        if conn:
            try:
                conn.close()
                logger.info("Closed Snowflake connection")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")


if __name__ == "__main__":
    run_pipeline()
