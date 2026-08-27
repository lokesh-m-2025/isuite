import os
from dataclasses import dataclass

@dataclass
class Config:
    """ETL Pipeline Configuration loaded from environment variables."""
    input_s3_path: str = os.getenv(
        "INPUT_S3_PATH",
        "s3://ignitho-development-bucket/input/sample-orders.csv"
    )
    output_s3_path: str = os.getenv(
        "OUTPUT_S3_PATH",
        "s3://ignitho-development-bucket/output/customer_totals.csv"
    )
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_session_token: str = os.getenv("AWS_SESSION_TOKEN", "")
