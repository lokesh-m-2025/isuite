import boto3
import io
import logging
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class S3Client:
    def __init__(self, bucket: str, region: str):
        self.bucket = bucket
        self.region = region
        self.client = boto3.client("s3", region_name=region)

    def find_latest_csv(self, prefix: str) -> Optional[Tuple[str, datetime]]:
        """
        Find the most recently modified CSV file in the given S3 prefix.
        Returns (key, last_modified_datetime) or (None, None) if not found.
        """
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket, Prefix=prefix, MaxKeys=1000
            )

            if "Contents" not in response:
                logger.warning(f"No files found in s3://{self.bucket}/{prefix}")
                return None, None

            csv_files = [
                obj for obj in response["Contents"] if obj["Key"].endswith(".csv")
            ]
            if not csv_files:
                logger.warning(f"No CSV files found in s3://{self.bucket}/{prefix}")
                return None, None

            latest = max(csv_files, key=lambda x: x["LastModified"])
            return latest["Key"], latest["LastModified"]

        except Exception as e:
            logger.error(f"Error listing S3 objects: {e}")
            raise

    def download_csv(self, key: str) -> io.BytesIO:
        """
        Download CSV file from S3 and return as BytesIO object.
        """
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return io.BytesIO(response["Body"].read())
        except Exception as e:
            logger.error(f"Error downloading s3://{self.bucket}/{key}: {e}")
            raise

    def record_processed_file(self, key: str, execution_id: str) -> None:
        """
        Record that a file has been processed by storing metadata in S3.
        This prevents duplicate processing on reruns.
        """
        try:
            metadata_key = f".pipeline_metadata/{execution_id}.txt"
            self.client.put_object(
                Bucket=self.bucket,
                Key=metadata_key,
                Body=f"Processed file: {key}\n".encode("utf-8"),
            )
            logger.info(f"Recorded processed file in {metadata_key}")
        except Exception as e:
            logger.error(f"Error recording processed file: {e}")
            raise
