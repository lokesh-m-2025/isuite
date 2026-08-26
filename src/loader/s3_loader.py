from pyspark.sql import DataFrame
from src.utils.logger import get_logger

logger = get_logger(__name__)


class S3Loader:
    @staticmethod
    def write_parquet(df: DataFrame, s3_path: str, partition_cols: list) -> int:
        record_count = df.count()
        if record_count == 0:
            logger.info("No valid records to write to target S3.")
            return 0
            
        logger.info(f"Writing {record_count} valid records to S3 path: {s3_path} partitioned by {partition_cols}")
        (
            df.write
            .mode("overwrite")
            .partitionBy(*partition_cols)
            .format("parquet")
            .save(s3_path)
        )
        logger.info("Successfully written output Parquet files.")
        return record_count

    @staticmethod
    def write_quarantine(df: DataFrame, quarantine_s3_path: str) -> int:
        quarantine_count = df.count()
        if quarantine_count == 0:
            logger.info("Zero records rejected during data validation.")
            return 0
            
        logger.warn(f"Writing {quarantine_count} invalid records to quarantine path: {quarantine_s3_path}")
        (
            df.write
            .mode("append")
            .format("json")
            .save(quarantine_s3_path)
        )
        return quarantine_count
