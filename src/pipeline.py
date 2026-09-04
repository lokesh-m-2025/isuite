"""Main ETL pipeline orchestration."""

import csv
import io
from datetime import datetime
from typing import Dict, List, Any, Tuple
from src.config import config
from src.logger import setup_logger, log_metrics
from src.s3_utils import S3Client
from src.schema import SchemaValidator, OrderSchema
from src.transformer import OrderTransformer
import logging

logger = setup_logger(__name__)


class ETLPipeline:
    """Main ETL pipeline for orders aggregation."""

    def __init__(self):
        """Initialize pipeline components."""
        self.s3_client = S3Client()
        self.execution_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.metrics = {
            "execution_id": self.execution_id,
            "start_time": datetime.utcnow().isoformat(),
            "records_read": 0,
            "records_valid": 0,
            "records_rejected": 0,
            "unique_customers": 0,
            "total_amount": 0.0,
        }
        self.rejected_records: List[Dict[str, str]] = []

    def check_idempotency(self) -> bool:
        """Check if this pipeline has already run today.

        Returns:
            True if already run today (should skip), False if should proceed
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        marker_path = config.marker_path

        if self.s3_client.file_exists(marker_path):
            try:
                marker_content = self.s3_client.read_file(marker_path)
                if marker_content.strip() == today:
                    logger.info(
                        f"Pipeline already executed today ({today}). Skipping to prevent duplicates."
                    )
                    return True
            except Exception as e:
                logger.warning(f"Failed to read idempotency marker: {e}. Proceeding.")

        return False

    def write_idempotency_marker(self) -> None:
        """Write execution marker to prevent duplicate runs."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        try:
            self.s3_client.write_file(config.marker_path, today)
            logger.info(f"Wrote idempotency marker for {today}")
        except Exception as e:
            logger.error(f"Failed to write idempotency marker: {e}")
            # Don't fail the pipeline for this

    def extract_records(
        self,
    ) -> Tuple[List[Dict[str, str]], int]:
        """Extract records from source CSV.

        Returns:
            Tuple of (records, total_count)
        """
        logger.info(f"Starting extraction from {config.input_path}")
        records = []
        total_count = 0

        try:
            content = self.s3_client.read_file(config.input_path)
            reader = csv.DictReader(io.StringIO(content))

            if not reader.fieldnames:
                raise ValueError("CSV file is empty or has no headers")

            for row in reader:
                if row:  # Skip empty rows
                    records.append(row)
                    total_count += 1

            self.metrics["records_read"] = total_count
            logger.info(f"Extracted {total_count} records from source")
            return records, total_count

        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            raise

    def validate_and_coerce(
        self, records: List[Dict[str, str]]
    ) -> Tuple[List[OrderSchema], List[Dict[str, str]]]:
        """Validate records and coerce to proper types.

        Args:
            records: Raw records from CSV

        Returns:
            Tuple of (valid_orders, rejected_raw_records)
        """
        logger.info(f"Validating {len(records)} records")
        valid_orders = []
        rejected_raw = []

        for idx, record in enumerate(records):
            # First pass: schema validation
            is_valid, error_msg = SchemaValidator.validate_record(record)

            if not is_valid:
                self.rejected_records.append(
                    {
                        "record_index": str(idx),
                        "record": str(record),
                        "rejection_reason": error_msg,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
                rejected_raw.append(record)
                self.metrics["records_rejected"] += 1
                logger.debug(f"Record {idx} rejected: {error_msg}")
                continue

            # Second pass: type coercion
            order_schema, coerce_error = SchemaValidator.coerce_types(record)

            if coerce_error:
                self.rejected_records.append(
                    {
                        "record_index": str(idx),
                        "record": str(record),
                        "rejection_reason": coerce_error,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
                rejected_raw.append(record)
                self.metrics["records_rejected"] += 1
                logger.debug(f"Record {idx} type coercion failed: {coerce_error}")
                continue

            valid_orders.append(order_schema)
            self.metrics["records_valid"] += 1

        logger.info(
            f"Validation complete: {len(valid_orders)} valid, "
            f"{len(rejected_raw)} rejected"
        )

        return valid_orders, rejected_raw

    def transform(
        self, valid_orders: List[OrderSchema]
    ) -> List[Dict[str, Any]]:
        """Transform valid orders into customer aggregates.

        Args:
            valid_orders: List of validated orders

        Returns:
            List of customer total records
        """
        logger.info(f"Transforming {len(valid_orders)} valid records")

        if not valid_orders:
            logger.warning("No valid records to transform")
            return []

        results, transform_metrics = OrderTransformer.aggregate_by_customer(
            valid_orders
        )
        self.metrics.update(transform_metrics)

        return results

    def load_output(
        self, customer_totals: List[Dict[str, Any]]
    ) -> bool:
        """Load aggregated results to output CSV.

        Args:
            customer_totals: List of customer total records

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Loading {len(customer_totals)} customer totals to output")

        try:
            csv_content = OrderTransformer.generate_csv_content(customer_totals)
            success = self.s3_client.write_file_with_retries(
                config.output_path, csv_content, content_type="text/csv"
            )

            if success:
                logger.info(f"Successfully loaded results to {config.output_path}")
            else:
                logger.error(f"Failed to load results after retries")

            return success

        except Exception as e:
            logger.error(f"Load failed: {e}", exc_info=True)
            return False

    def load_rejected(
        self, rejected_records: List[Dict[str, str]]
    ) -> bool:
        """Load rejected records to quarantine location.

        Args:
            rejected_records: List of records that failed validation

        Returns:
            True if successful, False otherwise
        """
        if not rejected_records:
            logger.info("No rejected records to save")
            return True

        logger.info(f"Saving {len(rejected_records)} rejected records")

        try:
            # Create CSV for rejected records
            lines = ["record_index,record,rejection_reason,timestamp"]

            for rejected in rejected_records:
                # Escape quotes in record field
                record_escaped = str(rejected.get("record", "")).replace('"', '""')
                reason_escaped = str(rejected.get("rejection_reason", "")).replace(
                    '"', '""'
                )

                lines.append(
                    f'{rejected.get("record_index", "")},'
                    f'"{record_escaped}",'
                    f'"{reason_escaped}",'
                    f'{rejected.get("timestamp", "")}'
                )

            csv_content = "\n".join(lines)
            rejected_path = (
                f"{config.rejected_path}customer_totals_rejected_{self.execution_id}.csv"
            )

            success = self.s3_client.write_file_with_retries(
                rejected_path, csv_content, content_type="text/csv"
            )

            if success:
                logger.info(f"Successfully saved rejected records to {rejected_path}")
            else:
                logger.error(f"Failed to save rejected records after retries")

            return success

        except Exception as e:
            logger.error(f"Failed to save rejected records: {e}", exc_info=True)
            return False

    def run(self) -> bool:
        """Execute the complete ETL pipeline.

        Returns:
            True if successful, False otherwise
        """
        logger.info("="* 80)
        logger.info(f"Starting ETL Pipeline (execution_id: {self.execution_id})")
        logger.info("="* 80)

        try:
            # Check idempotency
            if self.check_idempotency():
                logger.info("Pipeline execution skipped due to idempotency check")
                return True

            # Extract
            raw_records, _ = self.extract_records()
            if not raw_records:
                logger.warning("No records extracted from source")
                return False

            # Validate
            valid_orders, rejected_raw = self.validate_and_coerce(raw_records)

            # Transform
            customer_totals = self.transform(valid_orders)

            # Load output
            if customer_totals:
                output_success = self.load_output(customer_totals)
                if not output_success:
                    logger.error("Failed to load output")
                    return False
            else:
                logger.warning("No customer totals to load")
                return False

            # Load rejected
            self.load_rejected(self.rejected_records)

            # Write idempotency marker
            self.write_idempotency_marker()

            # Log final metrics
            self.metrics["end_time"] = datetime.utcnow().isoformat()
            self.metrics["status"] = "SUCCESS"

            log_metrics(
                logger,
                logging.INFO,
                "Pipeline execution completed successfully",
                self.metrics,
            )

            logger.info("="* 80)
            logger.info("Pipeline completed successfully")
            logger.info("="* 80)

            return True

        except Exception as e:
            self.metrics["end_time"] = datetime.utcnow().isoformat()
            self.metrics["status"] = "FAILED"
            self.metrics["error"] = str(e)

            log_metrics(
                logger,
                logging.ERROR,
                "Pipeline execution failed",
                self.metrics,
            )

            logger.error("="* 80)
            logger.error(f"Pipeline failed with error: {e}", exc_info=True)
            logger.error("="* 80)

            return False
