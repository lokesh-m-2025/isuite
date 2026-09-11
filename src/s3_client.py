"""S3 client wrapper with error handling."""

import logging
from io import BytesIO
from botocore.exceptions import BotoCoreError, ClientError

try:
    import boto3
except ImportError:
    raise ImportError("boto3 is required. Install with: pip install boto3")


class S3Client:
    """Wrapper around boto3 S3 client with error handling."""

    def __init__(self, region_name: str = "us-east-1", timeout_seconds: int = 30):
        """Initialize S3 client."""
        self.region_name = region_name
        self.timeout_seconds = timeout_seconds
        self.client = boto3.client(
            "s3",
            region_name=region_name,
            config=boto3.session.Config(
                connect_timeout=timeout_seconds,
                read_timeout=timeout_seconds,
                retries={"max_attempts": 3, "mode": "adaptive"},
            ),
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_object(self, bucket: str, key: str) -> bytes:
        """
        Retrieve object from S3.

        Returns:
            Object body as bytes.

        Raises:
            FileNotFoundError: If object does not exist.
            Exception: On S3 API errors.
        """
        try:
            self.logger.debug(f"Fetching s3://{bucket}/{key}")
            response = self.client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"s3://{bucket}/{key} does not exist")
            raise Exception(f"S3 get_object failed: {str(e)}") from e
        except BotoCoreError as e:
            raise Exception(f"S3 connection error: {str(e)}") from e

    def put_object(self, bucket: str, key: str, body: str | bytes) -> None:
        """
        Write object to S3.

        Args:
            bucket: S3 bucket name.
            key: S3 object key.
            body: Object content as string or bytes.

        Raises:
            Exception: On S3 API errors.
        """
        try:
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.logger.debug(f"Writing s3://{bucket}/{key}")
            self.client.put_object(Bucket=bucket, Key=key, Body=body)
        except ClientError as e:
            raise Exception(f"S3 put_object failed: {str(e)}") from e
        except BotoCoreError as e:
            raise Exception(f"S3 connection error: {str(e)}") from e

    def object_exists(self, bucket: str, key: str) -> bool:
        """
        Check if object exists in S3.

        Returns:
            True if object exists, False otherwise.
        """
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise
        except BotoCoreError:
            return False
