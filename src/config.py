import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    aws_access_key_id: str | None = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")
    source_s3_uri: str = os.getenv(
        "SOURCE_S3_URI", "s3://ignitho-development-bucket/input/sample-orders.csv"
    )
    target_s3_uri: str = os.getenv(
        "TARGET_S3_URI", "s3://ignitho-development-bucket/output/customer_totals_3.csv"
    )

    @classmethod
    def load(cls) -> "Config":
        return cls()
