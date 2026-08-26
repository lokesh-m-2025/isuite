import boto3
from datetime import datetime, timedelta
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WatermarkManager:
    def __init__(self, table_name: str, pipeline_id: str, region_name: str = "us-east-1"):
        self.table_name = table_name
        self.pipeline_id = pipeline_id
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.table = self.dynamodb.Table(self.table_name)

    def get_last_watermark(self, default_lookback_days: int = 30) -> str:
        try:
            response = self.table.get_item(Key={"pipeline_id": self.pipeline_id})
            if "Item" in response and "last_watermark" in response["Item"]:
                watermark = response["Item"]["last_watermark"]
                logger.info(f"Retrieved high watermark: {watermark} for pipeline {self.pipeline_id}")
                return watermark
        except Exception as e:
            logger.error(f"Failed to fetch watermark from DynamoDB: {str(e)}")
        
        default_wm = (datetime.utcnow() - timedelta(days=default_lookback_days)).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Using default fallback watermark: {default_wm}")
        return default_wm

    def update_watermark(self, new_watermark: str, record_count: int) -> None:
        try:
            self.table.put_item(
                Item={
                    "pipeline_id": self.pipeline_id,
                    "last_watermark": new_watermark,
                    "last_updated": datetime.utcnow().isoformat(),
                    "processed_record_count": record_count
                }
            )
            logger.info(f"Successfully updated watermark to {new_watermark} with {record_count} records.")
        except Exception as e:
            logger.error(f"Failed to update watermark in DynamoDB: {str(e)}")
            raise
