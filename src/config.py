"""Configuration management for the ETL pipeline.

All configuration is read from environment variables.
Sensitive values (credentials) are not logged.
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Centralized configuration for the ETL pipeline."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)

        # AWS Configuration
        self.aws_region: str = self._get_env("AWS_REGION", "us-east-1")
        self.s3_bucket_name: str = self._get_env("S3_BUCKET_NAME")

        # CloudWatch Logging Configuration
        self.log_group_name: str = self._get_env("LOG_GROUP_NAME")
        self.log_stream_name: str = self._get_env("LOG_STREAM_NAME")

        # S3 Paths (derived from bucket name)
        self.input_path: str = f"s3://{self.s3_bucket_name}/input/orders.csv"
        self.output_path: str = f"s3://{self.s3_bucket_name}/output/customer_totals.csv"
        self.rejected_path: str = f"s3://{self.s3_bucket_name}/rejected/"
        self.marker_path: str = f"s3://{self.s3_bucket_name}/.pipeline_markers/customer_totals_last_run.txt"

        # Pipeline Configuration
        self.batch_size: int = int(os.getenv("BATCH_SIZE", "1000"))
        self.max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
        self.retry_delay_seconds: int = int(os.getenv("RETRY_DELAY_SECONDS", "2"))

    @staticmethod
    def _get_env(key: str, default: Optional[str] = None) -> str:
        """Get environment variable with validation.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Environment variable value

        Raises:
            ValueError: If required variable is not set and no default provided
        """
        value = os.getenv(key, default)
        if not value:
            raise ValueError(f"Required environment variable '{key}' is not set")
        return value

    def validate(self) -> None:
        """Validate that all required configuration is set.

        Raises:
            ValueError: If critical configuration is missing
        """
        if not self.s3_bucket_name:
            raise ValueError("S3_BUCKET_NAME configuration is required")
        if not self.log_group_name:
            raise ValueError("LOG_GROUP_NAME configuration is required")
        if not self.log_stream_name:
            raise ValueError("LOG_STREAM_NAME configuration is required")


config = Config()
