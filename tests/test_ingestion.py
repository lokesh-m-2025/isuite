"""Tests for S3 file detection and CSV validation."""

import io
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.ingestion import OrdersCSVValidator, S3FileDetector


class TestS3FileDetector:
    """Tests for S3FileDetector."""

    @patch("boto3.client")
    def test_get_file_for_date_found(self, mock_boto_client):
        """Test successful file detection."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_object.return_value = {}

        detector = S3FileDetector(bucket="test-bucket", prefix="orders", region="us-east-1")
        result = detector.get_file_for_date(date(2024, 1, 15))

        assert result == "orders/orders_2024-01-15.csv"
        mock_s3.head_object.assert_called_once()

    @patch("boto3.client")
    def test_get_file_for_date_not_found(self, mock_boto_client):
        """Test when file does not exist."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.exceptions.NoSuchKey = Exception
        mock_s3.head_object.side_effect = Exception("NoSuchKey")

        detector = S3FileDetector(bucket="test-bucket", prefix="orders", region="us-east-1")
        result = detector.get_file_for_date(date(2024, 1, 15))

        assert result is None


class TestOrdersCSVValidator:
    """Tests for OrdersCSVValidator."""

    @patch("boto3.client")
    def test_validate_valid_csv(self, mock_boto_client):
        """Test validation of valid CSV."""
        csv_content = """order_id,customer_id,order_date,total_amount,status
ORD001,CUST001,2024-01-15,100.50,completed
ORD002,CUST002,2024-01-15,200.75,pending
"""

        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.get_object.return_value = {"Body": io.BytesIO(csv_content.encode())}

        validator = OrdersCSVValidator(
            bucket="test-bucket", key="orders_2024-01-15.csv", region="us-east-1"
        )
        valid, rejected = validator.validate()

        assert len(valid) == 2
        assert len(rejected) == 0
        assert valid[0]["order_id"] == "ORD001"
        assert valid[0]["total_amount"] == 100.50

    @patch("boto3.client")
    def test_validate_missing_fields(self, mock_boto_client):
        """Test validation rejects records with missing fields."""
        csv_content = """order_id,customer_id,order_date,total_amount,status
ORD001,CUST001,2024-01-15,,completed
ORD002,CUST002,2024-01-15,200.75,pending
"""

        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.get_object.return_value = {"Body": io.BytesIO(csv_content.encode())}

        validator = OrdersCSVValidator(
            bucket="test-bucket", key="orders_2024-01-15.csv", region="us-east-1"
        )
        valid, rejected = validator.validate()

        assert len(valid) == 1
        assert len(rejected) == 1
        assert "Missing required fields" in rejected[0]["error_message"]

    @patch("boto3.client")
    def test_validate_invalid_date_format(self, mock_boto_client):
        """Test validation rejects invalid date formats."""
        csv_content = """order_id,customer_id,order_date,total_amount,status
ORD001,CUST001,01/15/2024,100.50,completed
ORD002,CUST002,2024-01-15,200.75,pending
"""

        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.get_object.return_value = {"Body": io.BytesIO(csv_content.encode())}

        validator = OrdersCSVValidator(
            bucket="test-bucket", key="orders_2024-01-15.csv", region="us-east-1"
        )
        valid, rejected = validator.validate()

        assert len(valid) == 1
        assert len(rejected) == 1
        assert "Invalid order_date format" in rejected[0]["error_message"]

    @patch("boto3.client")
    def test_validate_invalid_amount(self, mock_boto_client):
        """Test validation rejects non-numeric amounts."""
        csv_content = """order_id,customer_id,order_date,total_amount,status
ORD001,CUST001,2024-01-15,not_a_number,completed
ORD002,CUST002,2024-01-15,200.75,pending
"""

        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.get_object.return_value = {"Body": io.BytesIO(csv_content.encode())}

        validator = OrdersCSVValidator(
            bucket="test-bucket", key="orders_2024-01-15.csv", region="us-east-1"
        )
        valid, rejected = validator.validate()

        assert len(valid) == 1
        assert len(rejected) == 1
        assert "Invalid total_amount" in rejected[0]["error_message"]
