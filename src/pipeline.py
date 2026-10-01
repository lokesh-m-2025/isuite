#!/usr/bin/env python3
"""
Daily orders S3 to Snowflake ELT pipeline.

Extracts orders CSV from S3, loads raw data into Snowflake staging,
and transforms using SQL. Implements incremental processing with
watermark-based deduplication and error handling.
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv

from src.config import load_config, Config
from src.ingestion import S3FileDetector, OrdersCSVValidator
from src.snowflake_client import SnowflakeConnection
from src.transformation import OrdersTransformer


load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main(target_date: Optional[str] = None):
    """
    Execute the daily orders pipeline.

    Args:
        target_date: Process a specific date (YYYY-MM-DD). Defaults to yesterday.
    """
    try:
        config = load_config()
        execution_date = (
            datetime.strptime(target_date, "%Y-%m-%d").date()
            if target_date
            else (datetime.utcnow() - timedelta(days=1)).date()
        )

        logger.info(f"Starting pipeline execution for date: {execution_date}")

        # Initialize connections and services
        sf_conn = SnowflakeConnection(
            account=config.snowflake_account,
            user=config.snowflake_user,
            password=config.snowflake_password,
            warehouse=config.snowflake_warehouse,
            database=config.snowflake_database,
            schema=config.snowflake_schema,
        )
        sf_conn.connect()

        try:
            # Initialize infrastructure
            _initialize_schema(sf_conn)

            # Check if already processed
            if _is_already_processed(sf_conn, execution_date):
                logger.info(
                    f"Date {execution_date} already successfully processed. "
                    "Skipping to prevent duplicates."
                )
                return

            # Detect and validate CSV file
            detector = S3FileDetector(
                bucket=config.s3_bucket,
                prefix=config.s3_prefix,
                region=config.aws_region,
            )
            s3_key = detector.get_file_for_date(execution_date)
            if not s3_key:
                logger.warning(f"No CSV file found for {execution_date}")
                _record_execution(sf_conn, execution_date, "NO_FILE_FOUND", 0, 0, 0)
                return

            logger.info(f"Processing file: s3://{config.s3_bucket}/{s3_key}")

            # Validate and load CSV
            validator = OrdersCSVValidator(
                bucket=config.s3_bucket,
                key=s3_key,
                region=config.aws_region,
            )
            valid_records, rejected_records = validator.validate()

            logger.info(
                f"Validation complete: {len(valid_records)} valid, "
                f"{len(rejected_records)} rejected"
            )

            # Load raw data into staging
            sf_conn.load_staging(
                table="ORDERS_STAGING",
                records=valid_records,
                execution_date=execution_date,
            )

            # Store rejected records
            if rejected_records:
                sf_conn.load_rejected_records(
                    table="REJECTED_RECORDS",
                    records=rejected_records,
                    execution_date=execution_date,
                )
                logger.info(f"Stored {len(rejected_records)} rejected records")

            # Transform and merge into final table
            transformer = OrdersTransformer(sf_conn)
            transformer.merge_orders(execution_date)

            # Record successful execution
            _record_execution(
                sf_conn,
                execution_date,
                "SUCCESS",
                len(valid_records),
                len(valid_records),
                len(rejected_records),
            )

            logger.info(
                f"Pipeline completed successfully for {execution_date}. "
                f"Loaded {len(valid_records)} records."
            )

        finally:
            sf_conn.close()

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


def _initialize_schema(sf_conn: SnowflakeConnection) -> None:
    """Create required tables if they don't exist."""
    sf_conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ORDERS_STAGING (
            ORDER_ID VARCHAR,
            CUSTOMER_ID VARCHAR,
            ORDER_DATE DATE,
            TOTAL_AMOUNT DECIMAL(10, 2),
            STATUS VARCHAR,
            RAW_RECORD VARIANT,
            LOAD_TIMESTAMP TIMESTAMP_NTZ,
            EXECUTION_DATE DATE
        )
    """
    )

    sf_conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ORDERS (
            ORDER_ID VARCHAR PRIMARY KEY,
            CUSTOMER_ID VARCHAR,
            ORDER_DATE DATE,
            TOTAL_AMOUNT DECIMAL(10, 2),
            STATUS VARCHAR,
            UPDATED_AT TIMESTAMP_NTZ,
            CREATED_AT TIMESTAMP_NTZ
        )
    """
    )

    sf_conn.execute(
        """
        CREATE TABLE IF NOT EXISTS REJECTED_RECORDS (
            REJECTED_ID VARCHAR,
            RAW_RECORD VARCHAR,
            ERROR_MESSAGE VARCHAR,
            REJECTED_AT TIMESTAMP_NTZ,
            EXECUTION_DATE DATE
        )
    """
    )

    sf_conn.execute(
        """
        CREATE TABLE IF NOT EXISTS PIPELINE_EXECUTION_LOG (
            EXECUTION_DATE DATE,
            STATUS VARCHAR,
            PROCESSED_COUNT INTEGER,
            SUCCESSFUL_COUNT INTEGER,
            REJECTED_COUNT INTEGER,
            EXECUTED_AT TIMESTAMP_NTZ
        )
    """
    )


def _is_already_processed(sf_conn: SnowflakeConnection, execution_date) -> bool:
    """Check if date has been successfully processed before."""
    result = sf_conn.fetch_one(
        f"""
        SELECT COUNT(*) as cnt FROM PIPELINE_EXECUTION_LOG
        WHERE EXECUTION_DATE = '{execution_date}' AND STATUS = 'SUCCESS'
    """
    )
    return result[0] > 0 if result else False


def _record_execution(
    sf_conn: SnowflakeConnection,
    execution_date,
    status: str,
    processed_count: int,
    successful_count: int,
    rejected_count: int,
) -> None:
    """Record pipeline execution in audit log."""
    sf_conn.execute(
        f"""
        INSERT INTO PIPELINE_EXECUTION_LOG
        (EXECUTION_DATE, STATUS, PROCESSED_COUNT, SUCCESSFUL_COUNT, REJECTED_COUNT, EXECUTED_AT)
        VALUES ('{execution_date}', '{status}', {processed_count}, {successful_count}, {rejected_count}, CURRENT_TIMESTAMP())
    """
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily orders ELT pipeline")
    parser.add_argument(
        "--date",
        type=str,
        help="Process specific date (YYYY-MM-DD). Defaults to yesterday.",
    )
    args = parser.parse_args()
    main(target_date=args.date)
