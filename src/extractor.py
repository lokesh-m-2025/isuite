import io
import logging
import pandas as pd
import boto3
from botocore.exceptions import ClientError
from src.config import PipelineConfig

logger = logging.getLogger(__name__)

class S3Extractor:
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

    def extract_csv(self, s3_uri: str) -> pd.DataFrame:
        bucket, key = PipelineConfig.parse_s3_uri(s3_uri)
        logger.info(f"Extracting CSV object from s3://{bucket}/{key}")
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            body = response["Body"].read()
            df = pd.read_csv(io.BytesIO(body))
            logger.info(f"Successfully extracted {len(df)} records from S3.")
            return df
        except ClientError as e:
            logger.error(f"AWS S3 client error during extraction: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse CSV file from S3: {e}")
            raise
