"""S3 file detection and CSV validation."""

import csv
import io
import logging
from datetime import date
from typing import List, Tuple

import boto3

logger = logging.getLogger(__name__)


class S3FileDetector:
    """Detects and retrieves orders CSV files from S3."""

    def __init__(self, bucket: str, prefix: str, region: str):
        self.bucket = bucket
        self.prefix = prefix
        self.s3_client = boto3.client("s3", region_name=region)

    def get_file_for_date(self, target_date: date) -> str:
        """
        Locate CSV file for a specific date.

        Expected naming: orders_YYYY-MM-DD.csv

        Args:
            target_date: Date to process

        Returns:
            S3 key if found, None otherwise.
        """
        expected_name = f"orders_{target_date.strftime('%Y-%m-%d')}.csv"
        key = f"{self.prefix.rstrip('/')}/{expected_name}"

        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=key)
            logger.info(f"Found file: {key}")
            return key
        except self.s3_client.exceptions.NoSuchKey:
            logger.warning(f"File not found: {key}")
            return None
        except Exception as e:
            logger.error(f"Error checking S3: {e}")
            raise


class OrdersCSVValidator:
    """Validates and parses orders CSV from S3."""

    REQUIRED_COLUMNS = ["order_id", "customer_id", "order_date", "total_amount", "status"]
    EXPECTED_COLUMNS = set(REQUIRED_COLUMNS)

    def __init__(self, bucket: str, key: str, region: str):
        self.bucket = bucket
        self.key = key
        self.s3_client = boto3.client("s3", region_name=region)

    def validate(self) -> Tuple[List[dict], List[dict]]:
        """
        Download and validate CSV from S3.

        Returns:
            Tuple of (valid_records, rejected_records)
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=self.key)
            content = response["Body"].read().decode("utf-8")
        except Exception as e:
            logger.error(f"Error reading S3 file: {e}")
            raise

        valid_records = []
        rejected_records = []

        try:
            reader = csv.DictReader(io.StringIO(content))
            if not reader.fieldnames:
                raise ValueError("CSV is empty")

            # Validate header
            actual_columns = set(k.lower() for k in reader.fieldnames if k)
            missing = self.EXPECTED_COLUMNS - actual_columns
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

            for row_num, row in enumerate(reader, start=2):
                record, error = self._validate_row(row, row_num)
                if error:
                    rejected_records.append(record)
                else:
                    valid_records.append(record)

        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            raise

        return valid_records, rejected_records

    def _validate_row(self, row: dict, row_num: int) -> Tuple[dict, bool]:
        """
        Validate a single CSV row.

        Returns:
            Tuple of (record_dict, has_error)
        """
        normalized_row = {k.lower(): v for k, v in row.items()}

        # Check for missing required fields
        missing_fields = [
            col for col in self.REQUIRED_COLUMNS if not normalized_row.get(col, "").strip()
        ]
        if missing_fields:
            return (
                {
                    "rejected_id": f"{self.key}_row_{row_num}",
                    "raw_record": str(row),
                    "error_message": f"Missing required fields: {missing_fields}",
                },
                True,
            )

        # Validate order_date format (YYYY-MM-DD)
        order_date = normalized_row["order_date"].strip()
        if not self._is_valid_date(order_date):
            return (
                {
                    "rejected_id": f"{self.key}_row_{row_num}",
                    "raw_record": str(row),
                    "error_message": f"Invalid order_date format: {order_date} (expected YYYY-MM-DD)",
                },
                True,
            )

        # Validate total_amount is numeric
        try:
            float(normalized_row["total_amount"])
        except ValueError:
            return (
                {
                    "rejected_id": f"{self.key}_row_{row_num}",
                    "raw_record": str(row),
                    "error_message": f"Invalid total_amount: {normalized_row['total_amount']}",
                },
                True,
            )

        # Valid record
        return (
            {
                "order_id": normalized_row["order_id"].strip(),
                "customer_id": normalized_row["customer_id"].strip(),
                "order_date": order_date,
                "total_amount": float(normalized_row["total_amount"]),
                "status": normalized_row["status"].strip(),
            },
            False,
        )

    @staticmethod
    def _is_valid_date(date_str: str) -> bool:
        """Check if string matches YYYY-MM-DD format."""
        try:
            from datetime import datetime
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
