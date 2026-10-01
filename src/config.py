"""Configuration management for the pipeline."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Pipeline configuration."""

    snowflake_account: str
    snowflake_user: str
    snowflake_password: str
    snowflake_warehouse: str
    snowflake_database: str
    snowflake_schema: str
    s3_bucket: str
    s3_prefix: str
    aws_region: str


def load_config() -> Config:
    """Load configuration from environment variables."""
    required_keys = [
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_WAREHOUSE",
        "SNOWFLAKE_DATABASE",
        "SNOWFLAKE_SCHEMA",
        "S3_BUCKET",
        "S3_PREFIX",
        "AWS_REGION",
    ]

    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")

    return Config(
        snowflake_account=os.getenv("SNOWFLAKE_ACCOUNT"),
        snowflake_user=os.getenv("SNOWFLAKE_USER"),
        snowflake_password=os.getenv("SNOWFLAKE_PASSWORD"),
        snowflake_warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        snowflake_database=os.getenv("SNOWFLAKE_DATABASE"),
        snowflake_schema=os.getenv("SNOWFLAKE_SCHEMA"),
        s3_bucket=os.getenv("S3_BUCKET"),
        s3_prefix=os.getenv("S3_PREFIX"),
        aws_region=os.getenv("AWS_REGION"),
    )
