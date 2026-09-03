import logging
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from src.config import PipelineConfig

logger = logging.getLogger(__name__)


def get_s3_client(config: PipelineConfig):
    boto_config = Config(
        retries={"max_attempts": 3, "mode": "standard"},
        connect_timeout=5,
        read_timeout=10
    )
    kwargs = {"region_name": config.aws_region, "config": boto_config}
    if config.aws_access_key_id and config.aws_secret_access_key:
        kwargs["aws_access_key_id"] = config.aws_access_key_id
        kwargs["aws_secret_access_key"] = config.aws_secret_access_key
        if config.aws_session_token:
            kwargs["aws_session_token"] = config.aws_session_token
    return boto3.client("s3", **kwargs)


def read_csv_from_s3(s3_client, bucket: str, key: str) -> str:
    logger.info(f"Downloading source file from s3://{bucket}/{key}")
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8")
        return content
    except ClientError as e:
        logger.error(f"Failed to read s3://{bucket}/{key}: {e}")
        raise


def write_csv_to_s3(s3_client, bucket: str, key: str, csv_data: str) -> None:
    logger.info(f"Uploading output file to s3://{bucket}/{key}")
    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=csv_data.encode("utf-8"),
            ContentType="text/csv"
        )
        logger.info(f"Successfully wrote output to s3://{bucket}/{key}")
    except ClientError as e:
        logger.error(f"Failed to write to s3://{bucket}/{key}: {e}")
        raise
