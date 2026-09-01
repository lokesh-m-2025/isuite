import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class PipelineConfig:
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    aws_access_key_id: str | None = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_session_token: str | None = os.getenv("AWS_SESSION_TOKEN")
    source_s3_uri: str = os.getenv(
        "SOURCE_S3_URI",
        "s3://ignitho-development-bucket/input/sample-orders.csv"
    )
    target_s3_uri: str = os.getenv(
        "TARGET_S3_URI",
        "s3://ignitho-development-bucket/output/customer_totals.csv"
    )

    @staticmethod
    def parse_s3_uri(s3_uri: str) -> tuple[str, str]:
        if not s3_uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI scheme: {s3_uri}")
        path_parts = s3_uri[5:].split("/", 1)
        if len(path_parts) != 2 or not path_parts[0] or not path_parts[1]:
            raise ValueError(f"Invalid S3 URI format: {s3_uri}")
        return path_parts[0], path_parts[1]
