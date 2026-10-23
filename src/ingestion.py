import os
import pandas as pd
from typing import Optional
from pathlib import Path


def read_csv_from_source(input_source: str, filename: str) -> pd.DataFrame:
    """
    Read CSV file from S3 or local filesystem.
    
    Args:
        input_source: S3 path (s3://bucket/prefix/) or local path (/path/to/dir/)
        filename: CSV filename to read
    
    Returns:
        pandas DataFrame
    
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If input_source format is invalid
    """
    if input_source.startswith("s3://"):
        return _read_from_s3(input_source, filename)
    else:
        return _read_from_local(input_source, filename)


def _read_from_local(directory: str, filename: str) -> pd.DataFrame:
    """Read CSV from local filesystem."""
    filepath = os.path.join(directory, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    df = pd.read_csv(filepath, encoding="utf-8")
    return df


def _read_from_s3(s3_prefix: str, filename: str) -> pd.DataFrame:
    """Read CSV from S3."""
    try:
        import boto3
    except ImportError:
        raise ImportError("boto3 required for S3 support. Install with: pip install boto3")

    s3_prefix = s3_prefix.rstrip("/")
    bucket, prefix = _parse_s3_path(s3_prefix)
    s3_key = f"{prefix}/{filename}" if prefix else filename

    try:
        s3_client = boto3.client("s3")
        response = s3_client.get_object(Bucket=bucket, Key=s3_key)
        df = pd.read_csv(response["Body"], encoding="utf-8")
        return df
    except s3_client.exceptions.NoSuchKey:
        raise FileNotFoundError(f"CSV file not found in S3: s3://{bucket}/{s3_key}")
    except Exception as e:
        raise RuntimeError(f"Failed to read from S3: {str(e)}")


def _parse_s3_path(s3_path: str) -> tuple[str, str]:
    """Parse S3 path into bucket and prefix."""
    if not s3_path.startswith("s3://"):
        raise ValueError(f"Invalid S3 path: {s3_path}")

    path_without_scheme = s3_path[5:]
    parts = path_without_scheme.split("/", 1)
    bucket = parts[0]
    prefix = parts[1] if len(parts) > 1 else ""
    return bucket, prefix.rstrip("/")
