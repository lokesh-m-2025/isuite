import sys
import os
import json
import argparse
from pyspark.sql import functions as F

from src.utils.spark_session import create_spark_session
from src.utils.logger import get_logger
from src.utils.watermark_manager import WatermarkManager
from src.validator.schema_validator import SchemaValidator
from src.transformer.sales_transformer import SalesTransformer
from src.loader.s3_loader import S3Loader

logger = get_logger("sap_sales_etl")


def run_pipeline(config_file: str, sap_jdbc_url: str, sap_user: str, sap_pass: str):
    logger.info("Starting SAP Sales ETL Pipeline Execution...")
    
    with open(config_file, "r") as f:
        config = json.load(f)
        
    spark = create_spark_session(config["app_name"])
    wm_manager = WatermarkManager(
        table_name=config["watermark"]["dynamodb_table"],
        pipeline_id=config["watermark"]["pipeline_id"]
    )
    
    last_watermark = wm_manager.get_last_watermark(config["watermark"]["default_lookback_days"])
    
    try:
        # Step 1: Ingestion from SAP
        logger.info(f"Extracting incremental sales data from SAP since {last_watermark}...")
        sap_query = f"""
            (SELECT VBELN, POSNR, ERDAT, AEDAT, NETWR, WAERK, KUNNR, MATNR 
             FROM VBAK 
             WHERE AEDAT >= '{last_watermark[:10]}' OR ERDAT >= '{last_watermark[:10]}') AS sap_sales
        """
        
        raw_df = spark.read \
            .format("jdbc") \
            .option("url", sap_jdbc_url) \
            .option("dbtable", sap_query) \
            .option("user", sap_user) \
            .option("password", sap_pass) \
            .option("numPartitions", config["source"]["num_partitions"]) \
            .option("fetchsize", config["source"]["jdbc_fetch_size"]) \
            .load()
            
        # Step 2: Validation & Quarantine
        valid_df, quarantine_df = SchemaValidator.validate_sales_data(raw_df)
        S3Loader.write_quarantine(quarantine_df, config["target"]["quarantine_s3_path"])
        
        # Step 3: Transformation
        transformed_df = SalesTransformer.transform(valid_df)
        
        # Step 4: Idempotent Load
        loaded_count = S3Loader.write_parquet(
            transformed_df,
            config["target"]["s3_path"],
            config["target"]["partition_cols"]
        )
        
        # Step 5: Update Watermark State
        if loaded_count > 0:
            max_timestamp_row = transformed_df.select(F.max("updated_timestamp")).collect()
            new_watermark = str(max_timestamp_row[0][0]) if max_timestamp_row and max_timestamp_row[0][0] else last_watermark
            wm_manager.update_watermark(new_watermark, loaded_count)
        else:
            logger.info("Pipeline finished successfully with 0 new records processed.")
            
    except Exception as e:
        logger.error(f"Pipeline execution failed with exception: {str(e)}")
        sys.exit(1)
    finally:
        spark.stop()
        logger.info("Spark Session terminated cleanly.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SAP Sales ETL Pipeline")
    parser.add_argument("--config", required=True, help="Path to pipeline config JSON")
    args = parser.parse_args()
    
    sap_jdbc_url = os.environ.get("SAP_JDBC_URL", "")
    sap_user = os.environ.get("SAP_DB_USER", "")
    sap_pass = os.environ.get("SAP_DB_PASSWORD", "")
    
    if not all([sap_jdbc_url, sap_user, sap_pass]):
        logger.error("Missing required SAP connection environment variables.")
        sys.exit(1)
        
    run_pipeline(args.config, sap_jdbc_url, sap_user, sap_pass)
