import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pandas as pd
import pytest
from src.pipeline import (
    read_csv_from_s3,
    load_raw_to_snowflake,
    quarantine_rejected_records,
    record_execution_metrics,
)


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    return MagicMock()


@pytest.fixture
def mock_snowflake_conn():
    """Create a mock Snowflake connection."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn


@pytest.fixture
def sample_csv_data():
    """Create sample CSV data as bytes."""
    csv_content = """order_id,customer_id,order_date,amount,currency,status
1,10,2024-01-01,100.50,USD,COMPLETED
2,20,2024-01-02,200.75,USD,PENDING
3,30,2024-01-03,150.00,EUR,CANCELLED
"""
    return csv_content.encode("utf-8")


def test_read_csv_from_s3(mock_s3_client, sample_csv_data):
    """Test reading CSV from S3."""
    from io import BytesIO
    mock_s3_client.get_object.return_value = {"Body": BytesIO(sample_csv_data)}

    df = read_csv_from_s3(mock_s3_client, "test-bucket", "test.csv")
    assert len(df) == 3
    assert list(df.columns) == [
        "order_id",
        "customer_id",
        "order_date",
        "amount",
        "currency",
        "status",
    ]


def test_load_raw_to_snowflake(mock_snowflake_conn):
    """Test loading data to Snowflake staging table."""
    df = pd.DataFrame({
        "order_id": [1, 2, 3],
        "customer_id": [10, 20, 30],
        "amount": [100.50, 200.75, 150.00],
    })

    from src.config import Config

    with patch.dict(os.environ, {
        "S3_BUCKET": "test-bucket",
        "S3_KEY": "test.csv",
        "SNOWFLAKE_ACCOUNT": "test",
        "SNOWFLAKE_USER": "user",
        "SNOWFLAKE_PASSWORD": "pass",
        "SNOWFLAKE_WAREHOUSE": "wh",
        "SNOWFLAKE_DATABASE": "db",
        "SNOWFLAKE_SCHEMA": "schema",
        "SNOWFLAKE_ROLE": "role",
    }):
        config = Config()
        loaded_count, rejected_count = load_raw_to_snowflake(
            mock_snowflake_conn, df, "test_schema.test_table", config
        )
        assert loaded_count == 3
        assert rejected_count == 0
        mock_snowflake_conn.cursor.return_value.execute.assert_called()
        mock_snowflake_conn.commit.assert_called()


def test_record_execution_metrics(mock_snowflake_conn):
    """Test recording pipeline execution metrics."""
    from src.config import Config

    with patch.dict(os.environ, {
        "S3_BUCKET": "test-bucket",
        "S3_KEY": "test.csv",
        "SNOWFLAKE_ACCOUNT": "test",
        "SNOWFLAKE_USER": "user",
        "SNOWFLAKE_PASSWORD": "pass",
        "SNOWFLAKE_WAREHOUSE": "wh",
        "SNOWFLAKE_DATABASE": "db",
        "SNOWFLAKE_SCHEMA": "schema",
        "SNOWFLAKE_ROLE": "role",
    }):
        config = Config()
        record_execution_metrics(
            mock_snowflake_conn, config, "SUCCESS", 100, 5, None
        )
        mock_snowflake_conn.cursor.return_value.execute.assert_called()
        mock_snowflake_conn.commit.assert_called()
