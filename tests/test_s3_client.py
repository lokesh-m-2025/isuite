"""Unit tests for S3 client."""

import unittest
from unittest.mock import Mock, patch, MagicMock

from botocore.exceptions import ClientError, BotoCoreError

from src.s3_client import S3Client


class TestS3Client(unittest.TestCase):
    """Test cases for S3Client."""

    @patch("src.s3_client.boto3.client")
    def setUp(self, mock_boto3_client):
        """Set up test fixtures."""
        self.mock_boto3_client = mock_boto3_client
        self.s3_client = S3Client(region_name="us-east-1", timeout_seconds=30)

    def test_get_object_success(self):
        """Test successful object retrieval."""
        mock_response = {"Body": MagicMock()}
        mock_response["Body"].read.return_value = b"test content"
        self.s3_client.client.get_object.return_value = mock_response

        result = self.s3_client.get_object("test-bucket", "test-key")
        self.assertEqual(result, b"test content")
        self.s3_client.client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="test-key"
        )

    def test_get_object_not_found(self):
        """Test get_object raises FileNotFoundError for missing objects."""
        error_response = {"Error": {"Code": "NoSuchKey"}}
        self.s3_client.client.get_object.side_effect = ClientError(
            error_response, "GetObject"
        )

        with self.assertRaises(FileNotFoundError):
            self.s3_client.get_object("test-bucket", "test-key")

    def test_put_object_success_string(self):
        """Test successful object write with string body."""
        self.s3_client.put_object("test-bucket", "test-key", "test content")
        self.s3_client.client.put_object.assert_called_once()
        call_kwargs = self.s3_client.client.put_object.call_args[1]
        self.assertEqual(call_kwargs["Bucket"], "test-bucket")
        self.assertEqual(call_kwargs["Key"], "test-key")
        self.assertEqual(call_kwargs["Body"], b"test content")

    def test_put_object_success_bytes(self):
        """Test successful object write with bytes body."""
        self.s3_client.put_object("test-bucket", "test-key", b"test content")
        self.s3_client.client.put_object.assert_called_once()

    def test_object_exists_true(self):
        """Test object_exists returns True for existing objects."""
        self.s3_client.client.head_object.return_value = {}
        result = self.s3_client.object_exists("test-bucket", "test-key")
        self.assertTrue(result)

    def test_object_exists_false(self):
        """Test object_exists returns False for missing objects."""
        error_response = {"Error": {"Code": "404"}}
        self.s3_client.client.head_object.side_effect = ClientError(
            error_response, "HeadObject"
        )
        result = self.s3_client.object_exists("test-bucket", "test-key")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
