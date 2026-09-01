import io
import logging
import pandas as pd
import boto3
from botocore.exceptions import ClientError
from src.config import PipelineConfig

logger = logging.getLogger(__name__)

class S3Loader:
    def __init__(self, config: PipelineConfig, s3_client=None):
        self.config = config
        if s3_client:
            self.s3_client = s3_client
        else:
            session_kwargs = {"region_name": config.aws_region}
            if config.aws_access_key_id and config.aws_secret_access_key:
                session_kwargs["aws_access_key_id"] = config.aws_access_key_id
                session_kwargs["aws_secret_access_key"] = config.aws_secret_access_key
            if config.aws_session_token:
                session_kwargs["aws_session_token"] = config.aws_session_token
            self.s3_client = boto3.client("s3", **session_kwargs)

    def load_csv(self, df: pd.DataFrame, target_s3_uri: str) -> None:
        bucket, key = PipelineConfig.parse_s3_uri(target_s3_uri)
        logger.info(f"Loading transformed results ({len(df)} rows) to s3://{bucket}/{key}")
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=csv_buffer.getvalue().encode("utf-8"),
                ContentType="text/csv"
            )
            logger.info("Load completed successfully.")
        except ClientError as e:
            logger.error(f"Failed to write CSV to S3: {e}")
            raise
