import io
import logging
from urllib.parse import urlparse
import boto3
from botocore.config import Config as BotoConfig
import pandas as pd
from src.config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_s3_uri(s3_uri: str) -> tuple[str, str]:
    parsed = urlparse(s3_uri)
    if parsed.scheme != "s3" or not parsed.netloc or not parsed.path:
        raise ValueError(f"Invalid S3 URI: {s3_uri}")
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    return bucket, key


def create_s3_client(config: Config):
    retry_config = BotoConfig(
        retries={"max_attempts": 5, "mode": "standard"}
    )
    kwargs = {"region_name": config.aws_region, "config": retry_config}
    if config.aws_access_key_id and config.aws_secret_access_key:
        kwargs["aws_access_key_id"] = config.aws_access_key_id
        kwargs["aws_secret_access_key"] = config.aws_secret_access_key
    return boto3.client("s3", **kwargs)


def extract(s3_client, s3_uri: str) -> pd.DataFrame:
    bucket, key = parse_s3_uri(s3_uri)
    logger.info(f"Fetching object from s3://{bucket}/{key}")
    response = s3_client.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read()
    df = pd.read_csv(io.BytesIO(body))
    logger.info(f"Successfully extracted {len(df)} raw records.")
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    required_cols = {"customer_id", "amount"}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError(f"Input data missing required columns: {required_cols - set(df.columns)}")

    # Validation & Cleaning
    clean_df = df.dropna(subset=["customer_id"]).copy()
    clean_df["amount"] = pd.to_numeric(clean_df["amount"], errors="coerce").fillna(0.0)

    # Transformation: Group by customer_id
    aggregated = (
        clean_df.groupby("customer_id", as_index=False)
        .agg(
            total_amount=("amount", "sum"),
            order_count=("amount", "count")
        )
    )
    aggregated["total_amount"] = aggregated["total_amount"].round(2)
    logger.info(f"Transformed data into {len(aggregated)} customer summary records.")
    return aggregated


def load(s3_client, df: pd.DataFrame, target_s3_uri: str) -> None:
    bucket, key = parse_s3_uri(target_s3_uri)
    out_buffer = io.StringIO()
    df.to_csv(out_buffer, index=False)
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=out_buffer.getvalue(),
        ContentType="text/csv"
    )
    logger.info(f"Successfully loaded aggregation results to s3://{bucket}/{key}")


def run_pipeline(config: Config | None = None) -> None:
    if config is None:
        config = Config.load()
    logger.info("Starting ETL pipeline execution.")
    s3_client = create_s3_client(config)
    raw_df = extract(s3_client, config.source_s3_uri)
    transformed_df = transform(raw_df)
    load(s3_client, transformed_df, config.target_s3_uri)
    logger.info("ETL pipeline completed successfully.")
