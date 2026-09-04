"""Integration tests for the ETL pipeline."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.pipeline import ETLPipeline
from src.schema import OrderSchema
import csv
import io


class TestETLPipeline:
    """Tests for ETLPipeline class."""

    def test_pipeline_init(self):
        """Test pipeline initialization."""
        pipeline = ETLPipeline()

        assert pipeline.execution_id is not None
        assert pipeline.metrics["records_read"] == 0
        assert pipeline.metrics["records_valid"] == 0
        assert pipeline.metrics["records_rejected"] == 0
        assert len(pipeline.rejected_records) == 0

    def test_validate_and_coerce_all_valid(self):
        """Test validation with all valid records."""
        pipeline = ETLPipeline()

        records = [
            {
                "order_id": "1",
                "customer_id": "cust_1",
                "amount": "50.00",
                "order_date": "2024-01-01",
            },
            {
                "order_id": "2",
                "customer_id": "cust_2",
                "amount": "75.00",
                "order_date": "2024-01-02",
            },
        ]

        valid_orders, rejected_raw = pipeline.validate_and_coerce(records)

        assert len(valid_orders) == 2
        assert len(rejected_raw) == 0
        assert pipeline.metrics["records_valid"] == 2
        assert pipeline.metrics["records_rejected"] == 0

    def test_validate_and_coerce_with_rejections(self):
        """Test validation with some invalid records."""
        pipeline = ETLPipeline()

        records = [
            {
                "order_id": "1",
                "customer_id": "cust_1",
                "amount": "50.00",
                "order_date": "2024-01-01",
            },
            {
                "order_id": "2",
                "customer_id": "",  # Invalid: empty customer_id
                "amount": "75.00",
                "order_date": "2024-01-02",
            },
            {
                "order_id": "3",
                "customer_id": "cust_3",
                "amount": "invalid",  # Invalid: non-numeric amount
                "order_date": "2024-01-03",
            },
        ]

        valid_orders, rejected_raw = pipeline.validate_and_coerce(records)

        assert len(valid_orders) == 1
        assert len(rejected_raw) == 2
        assert pipeline.metrics["records_valid"] == 1
        assert pipeline.metrics["records_rejected"] == 2
        assert len(pipeline.rejected_records) == 2

    def test_transform_with_valid_orders(self):
        """Test transformation of valid orders."""
        pipeline = ETLPipeline()

        orders = [
            OrderSchema(
                order_id="1", customer_id="cust_1", amount=50.0, order_date="2024-01-01"
            ),
            OrderSchema(
                order_id="2", customer_id="cust_1", amount=30.0, order_date="2024-01-02"
            ),
            OrderSchema(
                order_id="3", customer_id="cust_2", amount=100.0, order_date="2024-01-03"
            ),
        ]

        results = pipeline.transform(orders)

        assert len(results) == 2
        assert pipeline.metrics["unique_customers"] == 2
        assert pipeline.metrics["total_orders_aggregated"] == 3
        assert pipeline.metrics["total_amount"] == 180.0

    @patch("src.pipeline.S3Client")
    def test_check_idempotency_marker_exists(self, mock_s3_client):
        """Test idempotency check when marker exists for today."""
        pipeline = ETLPipeline()

        # Mock S3 client to return today's date as marker content
        mock_instance = MagicMock()
        mock_s3_client.return_value = mock_instance
        pipeline.s3_client = mock_instance

        from datetime import datetime

        today = datetime.utcnow().strftime("%Y-%m-%d")

        mock_instance.file_exists.return_value = True
        mock_instance.read_file.return_value = today

        # Create new pipeline to use mocked S3
        pipeline = ETLPipeline()
        pipeline.s3_client = mock_instance

        should_skip = pipeline.check_idempotency()

        assert should_skip is True
        mock_instance.file_exists.assert_called()

    @patch("src.pipeline.S3Client")
    def test_check_idempotency_no_marker(self, mock_s3_client):
        """Test idempotency check when no marker exists."""
        mock_instance = MagicMock()
        mock_s3_client.return_value = mock_instance
        mock_instance.file_exists.return_value = False

        pipeline = ETLPipeline()
        pipeline.s3_client = mock_instance

        should_skip = pipeline.check_idempotency()

        assert should_skip is False

    def test_load_rejected_empty_list(self):
        """Test loading rejected records with empty list."""
        with patch("src.pipeline.S3Client") as mock_s3_client:
            mock_instance = MagicMock()
            mock_s3_client.return_value = mock_instance

            pipeline = ETLPipeline()
            pipeline.s3_client = mock_instance

            result = pipeline.load_rejected([])

            assert result is True
            mock_instance.write_file_with_retries.assert_not_called()

    def test_load_rejected_with_records(self):
        """Test loading rejected records to S3."""
        with patch("src.pipeline.S3Client") as mock_s3_client:
            mock_instance = MagicMock()
            mock_s3_client.return_value = mock_instance
            mock_instance.write_file_with_retries.return_value = True

            pipeline = ETLPipeline()
            pipeline.s3_client = mock_instance

            rejected = [
                {
                    "record_index": "0",
                    "record": "{'order_id': '1'}",
                    "rejection_reason": "Missing customer_id",
                    "timestamp": "2024-01-01T00:00:00",
                },
            ]

            result = pipeline.load_rejected(rejected)

            assert result is True
            mock_instance.write_file_with_retries.assert_called_once()

            # Verify the call includes rejected data
            call_args = mock_instance.write_file_with_retries.call_args
            csv_content = call_args[0][1]
            assert "record_index,record,rejection_reason,timestamp" in csv_content
            assert "Missing customer_id" in csv_content
