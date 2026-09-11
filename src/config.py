"""Configuration management for ETL pipeline."""

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


@dataclass
class Config:
    """Pipeline configuration."""

    aws_region: str
    source_bucket: str
    source_key: str
    output_bucket: str
    output_prefix: str
    timeout_seconds: int


def load_config() -> Config:
    """
    Load configuration from environment variables.

    If .env file exists, load it first.
    """
    # Load .env file if python-dotenv is available
    env_path = Path(".env")
    if env_path.exists() and load_dotenv:
        load_dotenv(env_path)

    # Required configuration keys
    required_keys = [
        "AWS_REGION",
        "SOURCE_BUCKET",
        "SOURCE_KEY",
        "OUTPUT_BUCKET",
        "OUTPUT_PREFIX",
    ]

    # Check for required keys
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    if missing_keys:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_keys)}"
        )

    return Config(
        aws_region=os.getenv("AWS_REGION"),
        source_bucket=os.getenv("SOURCE_BUCKET"),
        source_key=os.getenv("SOURCE_KEY"),
        output_bucket=os.getenv("OUTPUT_BUCKET"),
        output_prefix=os.getenv("OUTPUT_PREFIX"),
        timeout_seconds=int(os.getenv("CONFIGURATION_TIMEOUT_SECONDS", "30")),
    )
