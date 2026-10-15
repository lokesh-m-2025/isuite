import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import pandas as pd


class TestPipelineExecution(unittest.TestCase):
    @patch("src.main.PipelineConfig")
    @patch("src.main.S3Client")
    @patch("src.main.SnowflakeClient")
    @patch("src.main.CSVValidator")
    def test_successful_pipeline_execution(
        self, mock_validator_class, mock_sf_class, mock_s3_class, mock_config_class
    ):
        """Test successful end-to-end pipeline execution."""
        from src.main import main

        # Setup mocks
        mock_config = Mock()
        mock_config.s3.bucket = "test-bucket"
        mock_config.s3.key_prefix = "orders/"
        mock_config.s3.region = "us-east-1"
        mock_config.staging_table = "orders_staging"
        mock_config.target_table = "orders"
        mock_config.quarantine_table = "orders_quarantine"
        mock_config.metadata_table = "pipeline_execution_log"
        mock_config_class.from_env.return_value = mock_config

        mock_s3 = Mock()
        mock_s3_class.return_value = mock_s3
        mock_s3.find_latest_csv.return_value = ("orders/2024-01-15.csv", datetime.now())

        mock_sf = Mock()
        mock_sf_class.return_value = mock_sf

        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator
        valid_df = pd.DataFrame(
            {
                "order_id": ["ORD001"],
                "customer_id": ["CUST001"],
                "order_date": ["2024-01-15"],
                "amount": ["150.50"],
                "status": ["completed"],
            }
        )
        mock_validator.validate_and_parse.return_value = (valid_df, [])

        # Execute pipeline
        result = main()

        # Assertions
        self.assertEqual(result, 0)
        mock_s3.find_latest_csv.assert_called_once_with("orders/")
        mock_sf.truncate_table.assert_called()
        mock_sf.insert_records.assert_called()
        mock_sf.record_execution.assert_called_once()

    @patch("src.main.PipelineConfig")
    @patch("src.main.S3Client")
    @patch("src.main.SnowflakeClient")
    def test_pipeline_no_csv_found(
        self, mock_sf_class, mock_s3_class, mock_config_class
    ):
        """Test pipeline when no CSV file is found in S3."""
        from src.main import main

        mock_config = Mock()
        mock_config.s3.bucket = "test-bucket"
        mock_config.s3.key_prefix = "orders/"
        mock_config.metadata_table = "pipeline_execution_log"
        mock_config_class.from_env.return_value = mock_config

        mock_s3 = Mock()
        mock_s3_class.return_value = mock_s3
        mock_s3.find_latest_csv.return_value = (None, None)

        mock_sf = Mock()
        mock_sf_class.return_value = mock_sf

        result = main()

        self.assertEqual(result, 1)
        mock_sf.record_execution.assert_called_once()

    @patch("src.main.PipelineConfig")
    @patch("src.main.S3Client")
    @patch("src.main.SnowflakeClient")
    @patch("src.main.CSVValidator")
    def test_pipeline_with_malformed_records(
        self, mock_validator_class, mock_sf_class, mock_s3_class, mock_config_class
    ):
        """Test pipeline with malformed records."""
        from src.main import main

        mock_config = Mock()
        mock_config.s3.bucket = "test-bucket"
        mock_config.s3.key_prefix = "orders/"
        mock_config.staging_table = "orders_staging"
        mock_config.target_table = "orders"
        mock_config.quarantine_table = "orders_quarantine"
        mock_config.metadata_table = "pipeline_execution_log"
        mock_config_class.from_env.return_value = mock_config

        mock_s3 = Mock()
        mock_s3_class.return_value = mock_s3
        mock_s3.find_latest_csv.return_value = ("orders/2024-01-15.csv", datetime.now())

        mock_sf = Mock()
        mock_sf_class.return_value = mock_sf

        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator
        valid_df = pd.DataFrame(
            {
                "order_id": ["ORD001"],
                "customer_id": ["CUST001"],
                "order_date": ["2024-01-15"],
                "amount": ["150.50"],
                "status": ["completed"],
            }
        )
        malformed = [
            {
                "row_number": 3,
                "row_data": {"order_id": "ORD002", "customer_id": ""},
                "error_reason": "Contains empty strings",
            }
        ]
        mock_validator.validate_and_parse.return_value = (valid_df, malformed)

        result = main()

        self.assertEqual(result, 0)
        # Verify malformed records were inserted into quarantine
        calls = mock_sf.insert_records.call_args_list
        self.assertTrue(
            any(
                "orders_quarantine" in str(call) for call in calls
            ),
            "Quarantine table should have been populated",
        )


if __name__ == "__main__":
    unittest.main()
