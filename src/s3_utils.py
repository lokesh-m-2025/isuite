"""AWS S3 utilities for reading and writing files."""

import io
from typing import Iterator, Optional, Tuple
import boto3
from botocore.exceptions import ClientError
from src.config import config
from src.logger import setup_logger

logger = setup_logger(__name__)


class S3Client:
    """Wrapper around boto3 S3 client with retry logic."""

    def __init__(self):
        """Initialize S3 client."""
        self.client = boto3.client("s3", region_name=config.aws_region)

    def parse_s3_path(self, s3_path: str) -> Tuple[str, str]:
        """Parse S3 path into bucket and key.

        Args:
            s3_path: Path like s3://bucket/path/to/file

        Returns:
            Tuple of (bucket_name, key)

        Raises:
            ValueError: If path is invalid
        """
        if not s3_path.startswith("s3://"):
            raise ValueError(f"Invalid S3 path format: {s3_path}")

        parts = s3_path[5:].split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 path format: {s3_path}")

        return parts[0], parts[1]

    def file_exists(self, s3_path: str) -> bool:
        """Check if a file exists in S3.

        Args:
            s3_path: S3 path to check

        Returns:
            True if file exists, False otherwise
        """
        try:
            bucket, key = self.parse_s3_path(s3_path)
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    def read_file(self, s3_path: str) -> str:
        """Read entire file from S3.

        Args:
            s3_path: S3 path to read

        Returns:
            File contents as string

        Raises:
            Exception: If read fails
        """
        bucket, key = self.parse_s3_path(s3_path)

        try:
            response = self.client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read().decode("utf-8")
        except ClientError as e:
            logger.error(f"Failed to read S3 file {s3_path}: {e}")
            raise

    def read_file_lines(self, s3_path: str) -> Iterator[str]:
        """Read file from S3 line by line.

        Args:
            s3_path: S3 path to read

        Yields:
            Lines from the file

        Raises:
            Exception: If read fails
        """
        bucket, key = self.parse_s3_path(s3_path)

        try:
            response = self.client.get_object(Bucket=bucket, Key=key)
            for line in response["Body"].iter_lines():
                yield line.decode("utf-8")
        except ClientError as e:
            logger.error(f"Failed to read S3 file {s3_path}: {e}")
            raise

    def write_file(
        self, s3_path: str, content: str, content_type: str = "text/plain"
    ) -> None:
        """Write content to S3 file.

        Args:
            s3_path: S3 path to write to
            content: File contents as string
            content_type: MIME type for the file

        Raises:
            Exception: If write fails
        """
        bucket, key = self.parse_s3_path(s3_path)

        try:
            self.client.put_object(
                Bucket=bucket, Key=key, Body=content, ContentType=content_type
            )
            logger.info(f"Successfully wrote file to {s3_path}")
        except ClientError as e:
            logger.error(f"Failed to write S3 file {s3_path}: {e}")
            raise

    def write_file_with_retries(
        self, s3_path: str, content: str, content_type: str = "text/plain"
    ) -> bool:
        """Write content to S3 file with retry logic.

        Args:
            s3_path: S3 path to write to
            content: File contents as string
            content_type: MIME type for the file

        Returns:
            True if successful, False if all retries exhausted
        """
        import time

        for attempt in range(config.max_retries):
            try:
                self.write_file(s3_path, content, content_type)
                return True
            except Exception as e:
                if attempt < config.max_retries - 1:
                    wait_time = config.retry_delay_seconds * (2 ** attempt)
                    logger.warning(
                        f"Write to {s3_path} failed (attempt {attempt + 1}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Failed to write to {s3_path} after {config.max_retries} attempts: {e}"
                    )
                    return False

        return False

    def delete_file(self, s3_path: str) -> bool:
        """Delete a file from S3.

        Args:
            s3_path: S3 path to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            bucket, key = self.parse_s3_path(s3_path)
            self.client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Successfully deleted file {s3_path}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete S3 file {s3_path}: {e}")
            return False
