import os
from typing import Optional


class Config:
    """Configuration for the ETL pipeline."""

    def __init__(
        self,
        source_bucket: str,
        source_key: str,
        target_bucket: str,
        target_key: str,
        aws_region: str = "us-east-1",
        log_file_path: str = "etl_pipeline.log",
        required_columns: Optional[list] = None,
    ):
        self.source_bucket = source_bucket
        self.source_key = source_key
        self.target_bucket = target_bucket
        self.target_key = target_key
        self.aws_region = aws_region
        self.log_file_path = log_file_path
        self.required_columns = required_columns or ["customer_id", "amount"]

    @classmethod
    def from_environment(cls) -> "Config":
        """Create Config from environment variables.
        
        Raises:
            ValueError: if required environment variables are missing
        """
        source_bucket = os.getenv("SOURCE_BUCKET")
        source_key = os.getenv("SOURCE_KEY")
        target_bucket = os.getenv("TARGET_BUCKET")
        target_key = os.getenv("TARGET_KEY")
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        log_file_path = os.getenv("LOG_FILE_PATH", "etl_pipeline.log")

        missing = []
        if not source_bucket:
            missing.append("SOURCE_BUCKET")
        if not source_key:
            missing.append("SOURCE_KEY")
        if not target_bucket:
            missing.append("TARGET_BUCKET")
        if not target_key:
            missing.append("TARGET_KEY")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        return cls(
            source_bucket=source_bucket,
            source_key=source_key,
            target_bucket=target_bucket,
            target_key=target_key,
            aws_region=aws_region,
            log_file_path=log_file_path,
        )
