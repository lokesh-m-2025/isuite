import pytest
import tempfile
import os
import pandas as pd
from src.ingestion import read_csv_from_source, _parse_s3_path


class TestReadCSVFromLocal:
    """Test reading CSV from local filesystem."""

    def test_read_valid_local_csv(self):
        """Test reading valid CSV from local path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "test.csv")
            df = pd.DataFrame({
                "order_id": ["ORD-001", "ORD-002"],
                "customer_id": ["CUST-001", "CUST-002"],
                "order_date": ["2024-01-15", "2024-01-16"],
                "amount": [100.0, 200.0],
                "status": ["completed", "pending"]
            })
            df.to_csv(csv_path, index=False)

            result = read_csv_from_source(tmpdir, "test.csv")
            assert len(result) == 2
            assert list(result.columns) == ["order_id", "customer_id", "order_date", "amount", "status"]

    def test_read_missing_file(self):
        """Test error when file does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                read_csv_from_source(tmpdir, "nonexistent.csv")


class TestParseS3Path:
    """Test S3 path parsing."""

    def test_parse_s3_path_with_prefix(self):
        """Test parsing S3 path with prefix."""
        bucket, prefix = _parse_s3_path("s3://my-bucket/data/orders/")
        assert bucket == "my-bucket"
        assert prefix == "data/orders"

    def test_parse_s3_path_no_prefix(self):
        """Test parsing S3 path without prefix."""
        bucket, prefix = _parse_s3_path("s3://my-bucket/")
        assert bucket == "my-bucket"
        assert prefix == ""

    def test_parse_invalid_s3_path(self):
        """Test error with invalid S3 path."""
        with pytest.raises(ValueError):
            _parse_s3_path("/local/path/")
