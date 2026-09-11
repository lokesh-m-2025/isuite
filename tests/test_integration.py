import unittest
import tempfile
import os
from io import StringIO
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

from config import Config
from etl_pipeline import OrdersETLPipeline


class TestOrdersETLPipeline(unittest.TestCase):
    """Integration tests for OrdersETLPipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = Config(
            source_bucket="test-bucket",
            source_key="input/orders.csv",
            target_bucket="test-bucket",
            target_key="output/customer_totals.csv",
            aws_region="us-east-1",
            log_file_path=tempfile.mktemp(suffix=".log"),
        )

    def tearDown(self):
        """Clean up test artifacts."""
        if os.path.exists(self.config.log_file_path):
            os.remove(self.config.log_file_path)

    @patch("etl_pipeline.boto3.client")
    def test_full_pipeline_success(self, mock_boto_client):
        """Test successful execution of full pipeline."""
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Mock source CSV
        source_csv = "customer_id,amount\nC001,100.0\nC001,50.0\nC002,200.0"
        mock_s3.get_object.return_value = {"Body": StringIO(source_csv)}
        
        # Run pipeline
        pipeline = OrdersETLPipeline(self.config)
        metrics = pipeline.run()
        
        # Verify success
        self.assertEqual(metrics["status"], "SUCCESS")
        self.assertEqual(metrics["source_rows"], 3)
        self.assertEqual(metrics["valid_rows"], 3)
        self.assertEqual(metrics["invalid_rows"], 0)
        self.assertEqual(metrics["output_rows"], 2)
        
        # Verify S3 put_object was called
        mock_s3.put_object.assert_called_once()
        call_kwargs = mock_s3.put_object.call_args[1]
        self.assertEqual(call_kwargs["Bucket"], self.config.target_bucket)
        self.assertEqual(call_kwargs["Key"], self.config.target_key)
        
        # Verify output content
        output_csv = call_kwargs["Body"]
        self.assertIn("customer_id", output_csv)
        self.assertIn("total_amount", output_csv)
        self.assertIn("order_count", output_csv)
        self.assertIn("C001", output_csv)
        self.assertIn("C002", output_csv)

    @patch("etl_pipeline.boto3.client")
    def test_pipeline_with_invalid_records(self, mock_boto_client):
        """Test pipeline handling of invalid records."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        # Source CSV with invalid records
        source_csv = (
            "customer_id,amount\n"
            "C001,100.0\n"
            "C002,invalid\n"  # invalid amount
            "C003,200.0"
        )
        mock_s3.get_object.return_value = {"Body": StringIO(source_csv)}
        
        pipeline = OrdersETLPipeline(self.config)
        metrics = pipeline.run()
        
        self.assertEqual(metrics["status"], "SUCCESS")
        self.assertEqual(metrics["source_rows"], 3)
        self.assertEqual(metrics["valid_rows"], 2)
        self.assertEqual(metrics["invalid_rows"], 1)
        self.assertEqual(metrics["output_rows"], 2)

    @patch("etl_pipeline.boto3.client")
    def test_pipeline_read_error(self, mock_boto_client):
        """Test pipeline handling of read errors."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.get_object.side_effect = Exception("S3 read error")
        
        pipeline = OrdersETLPipeline(self.config)
        metrics = pipeline.run()
        
        self.assertEqual(metrics["status"], "FAILED")
        self.assertIsNotNone(metrics["error"])
        self.assertIn("S3 read error", metrics["error"])

    @patch("etl_pipeline.boto3.client")
    def test_pipeline_write_error(self, mock_boto_client):
        """Test pipeline handling of write errors."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        source_csv = "customer_id,amount\nC001,100.0"
        mock_s3.get_object.return_value = {"Body": StringIO(source_csv)}
        mock_s3.put_object.side_effect = Exception("S3 write error")
        
        pipeline = OrdersETLPipeline(self.config)
        metrics = pipeline.run()
        
        self.assertEqual(metrics["status"], "FAILED")
        self.assertIsNotNone(metrics["error"])
        self.assertIn("S3 write error", metrics["error"])


if __name__ == "__main__":
    unittest.main()
