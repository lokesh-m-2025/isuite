import logging
from pyspark.sql import DataFrame
from src.config import PipelineConfig

logger = logging.getLogger(__name__)

class S3DataWriter:
    """Handles idempotent writes to Amazon S3 data lake."""
    def __init__(self, config: PipelineConfig):
        self.config = config

    def write_curated(self, df: DataFrame) -> None:
        """Writes clean, transformed sales data partitioned by year and month."""
        if df.rdd.isEmpty():
            logger.info("No clean sales records to write to S3.")
            return
            
        target_path = self.config.s3_target_path
        logger.info(f"Writing curated dataset to {target_path}")
        
        df.write \
            .mode("overwrite") \
            .format("parquet") \
            .partitionBy("sales_year", "sales_month") \
            .option("partitionOverwriteMode", "dynamic") \
            .save(target_path)
        
        logger.info("Curated data write successfully completed.")

    def write_quarantine(self, df: DataFrame) -> None:
        """Writes rejected invalid records to quarantine directory."""
        if df.rdd.isEmpty():
            logger.info("No quarantine records detected.")
            return
            
        quarantine_path = self.config.s3_quarantine_path
        logger.warning(f"Writing rejected records to quarantine at {quarantine_path}")
        
        df.write \
            .mode("append") \
            .format("parquet") \
            .save(quarantine_path)
