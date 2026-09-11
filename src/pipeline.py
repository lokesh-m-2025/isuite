#!/usr/bin/env python3
"""
Order Aggregation ETL Pipeline.

Reads orders from S3, validates and aggregates by customer_id,
writes customer totals back to S3.
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

from config import load_config
from s3_client import S3Client
from etl import OrderAggregationETL


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure logging with timestamp and level."""
    logger = logging.getLogger("etl_pipeline")
    logger.setLevel(getattr(logging, log_level))
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def main():
    """Execute the order aggregation ETL pipeline."""
    logger = setup_logging()
    execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Pipeline execution started: {execution_id}")

    try:
        # Load configuration from environment
        config = load_config()
        logger.info(f"Configuration loaded from .env")

        # Initialize S3 client
        s3_client = S3Client(
            region_name=config.aws_region,
            timeout_seconds=config.timeout_seconds,
        )
        logger.info(f"S3 client initialized for region {config.aws_region}")

        # Initialize ETL processor
        etl = OrderAggregationETL(s3_client=s3_client, logger=logger)

        # Execute ETL pipeline
        execution_result = etl.run(
            source_bucket=config.source_bucket,
            source_key=config.source_key,
            output_bucket=config.output_bucket,
            output_prefix=config.output_prefix,
            execution_id=execution_id,
        )

        # Log execution results
        logger.info(
            f"Pipeline execution completed: {execution_result['status']}"
        )
        logger.info(f"Records processed: {execution_result['total_records']}")
        logger.info(f"Records aggregated: {execution_result['aggregated_records']}")
        logger.info(f"Records rejected: {execution_result['rejected_records']}")
        logger.info(
            f"Output: s3://{config.output_bucket}/{execution_result['output_key']}"
        )

        if execution_result["rejected_records"] > 0:
            logger.warning(
                f"Rejected records written to: "
                f"s3://{config.output_bucket}/{execution_result['rejection_key']}"
            )

        # Write execution metadata
        metadata_key = f"{config.output_prefix}/execution_log_{execution_id}.json"
        s3_client.put_object(
            bucket=config.output_bucket,
            key=metadata_key,
            body=json.dumps(execution_result, indent=2, default=str),
        )
        logger.info(f"Execution metadata written to: s3://{config.output_bucket}/{metadata_key}")

        return 0

    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
