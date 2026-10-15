import unittest
from unittest.mock import Mock, patch, MagicMock
from src.snowflake_client import SnowflakeClient
from src.config import SnowflakeConfig
import os


class TestSnowflakeClient(unittest.TestCase):
    def setUp(self):
        # Use environment variables or test fixtures instead of hardcoded credentials
        self.config = SnowflakeConfig(
            account=os.getenv("TEST_SNOWFLAKE_ACCOUNT", "test_account"),
            user=os.getenv("TEST_SNOWFLAKE_USER", "test_user"),
            password=os.getenv("TEST_SNOWFLAKE_PASSWORD", "test_password"),
            database="test_db",
            schema="test_schema",
            warehouse="test_warehouse",
            role="test_role",
        )

    @patch("snowflake.connector.connect")
    def test_connect(self, mock_connect):
        """Test Snowflake connection."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        client = SnowflakeClient(self.config)
        client.connect()

        mock_connect.assert_called_once_with(
            user=self.config.user,
            password=self.config.password,
            account=self.config.account,
            warehouse=self.config.warehouse,
            database=self.config.database,
            schema=self.config.schema,
            role=self.config.role,
        )
        self.assertEqual(client.conn, mock_conn)

    @patch("snowflake.connector.connect")
    def test_insert_records(self, mock_connect):
        """Test batch insert of records."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        client = SnowflakeClient(self.config)
        client.conn = mock_conn

        records = [
            {"order_id": "ORD001", "amount": "150.50"},
            {"order_id": "ORD002", "amount": "200.00"},
        ]

        result = client.insert_records("orders", records)

        self.assertEqual(result, 2)
        self.assertEqual(mock_cursor.execute.call_count, 2)
        mock_conn.commit.assert_called_once()

    @patch("snowflake.connector.connect")
    def test_insert_empty_records(self, mock_connect):
        """Test insert with no records."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        client = SnowflakeClient(self.config)
        client.conn = mock_conn

        result = client.insert_records("orders", [])

        self.assertEqual(result, 0)
        mock_conn.cursor.assert_not_called()

    @patch("snowflake.connector.connect")
    def test_truncate_table(self, mock_connect):
        """Test table truncation."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        client = SnowflakeClient(self.config)
        client.conn = mock_conn

        client.truncate_table("orders")

        mock_cursor.execute.assert_called_with("TRUNCATE TABLE orders")

    @patch("snowflake.connector.connect")
    def test_disconnect(self, mock_connect):
        """Test disconnection."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        client = SnowflakeClient(self.config)
        client.conn = mock_conn

        client.disconnect()

        mock_conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
