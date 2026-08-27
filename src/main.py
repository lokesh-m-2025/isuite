import sys
from src.config import Config
from src.schemas import ORDERS_SCHEMA
from src.transformations import aggregate_customer_totals
from src.utils import get_logger, init_spark_session

def run_pipeline() -> None:
    logger = get_logger()
    config = Config()

    logger.info("Initializing Spark Session...")
    spark = init_spark_session(config)

    try:
        logger.info(f"Reading order records from S3: {config.input_s3_path}")
        raw_df = spark.read \
            .option("header", "true") \
            .schema(ORDERS_SCHEMA) \
            .csv(config.input_s3_path)

        total_raw = raw_df.count()
        logger.info(f"Extracted {total_raw} raw records from source file.")

        logger.info("Executing aggregation transformations...")
        transformed_df = aggregate_customer_totals(raw_df)

        transformed_count = transformed_df.count()
        logger.info(f"Transformation complete. Aggregated customer records: {transformed_count}")

        logger.info(f"Writing output results to S3: {config.output_s3_path}")
        transformed_df.coalesce(1) \
            .write \
            .mode("overwrite") \
            .option("header", "true") \
            .csv(config.output_s3_path)

        logger.info("ETL Pipeline completed successfully. Source file unchanged.")

    except Exception as exc:
        logger.error(f"Pipeline failed with error: {str(exc)}", exc_info=True)
        sys.exit(1)
    finally:
        spark.stop()

if __name__ == "__main__":
    run_pipeline()
