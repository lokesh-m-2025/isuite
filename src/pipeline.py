import sys
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.config import PipelineConfig
from src.watermark import WatermarkManager
from src.sap_connector import SAPExtractor
from src.transformations import SalesDataTransformer
from src.s3_writer import S3DataWriter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SAP_ETL_Pipeline")

def build_spark_session(app_name: str) -> SparkSession:
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
        .getOrCreate()

def run_pipeline():
    config = PipelineConfig()
    spark = build_spark_session(config.app_name)
    
    logger.info(f"Starting ETL pipeline run on environment: {config.env}")
    
    try:
        # 1. Fetch Watermark
        wm_manager = WatermarkManager(spark, config.s3_watermark_path, config.default_lookback_days)
        last_wm = wm_manager.get_last_watermark()
        
        # 2. Extract Data from SAP
        extractor = SAPExtractor(spark, config)
        raw_df = extractor.extract_sales_orders(last_wm)
        
        record_count = raw_df.count()
        logger.info(f"Extracted {record_count} records from SAP source.")
        
        if record_count == 0:
            logger.info("No new or updated records found. Terminating execution successfully.")
            return
            
        # 3. Validation & Quarantine
        valid_df, invalid_df = SalesDataTransformer.validate_and_split(raw_df)
        
        writer = S3DataWriter(config)
        writer.write_quarantine(invalid_df)
        
        # 4. Transform Valid Data
        curated_df = SalesDataTransformer.transform(valid_df)
        curated_df.persist()
        
        # 5. Write Curated Output to S3
        writer.write_curated(curated_df)
        
        # 6. Compute & Advance Watermark
        max_updated_at = curated_df.select(F.max("updated_at")).collect()[0][0]
        if max_updated_at:
            new_watermark_str = max_updated_at.strftime("%Y-%m-%d %H:%M:%S")
            wm_manager.update_watermark(new_watermark_str)
            
        curated_df.unpersist()
        logger.info("SAP Sales ETL Pipeline executed successfully.")
        
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {str(e)}", exc_info=True)
        spark.stop()
        sys.exit(1)
    finally:
        spark.stop()

if __name__ == "__main__":
    run_pipeline()
