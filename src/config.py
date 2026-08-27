import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

class Config:
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    S3_SOURCE_URI = os.getenv("S3_SOURCE_URI", "s3://ignitho-development-bucket/input/sample-orders.csv")
    S3_TARGET_URI = os.getenv("S3_TARGET_URI", "s3://ignitho-development-bucket/output/customer_totals.csv")

    @staticmethod
    def parse_s3_uri(uri: str):
        parsed = urlparse(uri)
        if parsed.scheme != "s3":
            raise ValueError(f"Invalid S3 URI scheme: {uri}")
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        return bucket, key
