"""PySpark job for extracting order data from S3, aggregating totals per customer, and writing results back to S3."""
import argparse
import logging
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, round as _round, sum as _sum
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("orders_etl")

ORDERS_SCHEMA = StructType([
    StructField("order_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("order_date", StringType(), True),
    StructField("amount", DoubleType(), True),
])


def create_spark_session(app_name: str = "OrdersAggregationETL") -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .getOrCreate()
    )


def extract_orders(spark: SparkSession, input_path: str):
    logger.info(f"Extracting raw orders CSV from S3 path: {input_path}")
    try:
        return (
            spark.read.format("csv")
            .option("header", "true")
            .schema(ORDERS_SCHEMA)
            .option("mode", "PERMISSIVE")
            .load(input_path)
        )
    except Exception as err:
        logger.error(f"Failed to read orders from S3: {err}")
        raise


def transform_customer_totals(df):
    logger.info("Aggregating order statistics by customer_id...")
    valid_df = df.filter(
        col("customer_id").isNotNull()
        & (col("customer_id") != "")
        & col("amount").isNotNull()
        & (col("amount") >= 0)
    )
    return (
        valid_df.groupBy("customer_id")
        .agg(
            _round(_sum("amount"), 2).alias("total_amount"),
            count("order_id").alias("order_count"),
        )
        .orderBy("customer_id")
    )


def load_customer_totals(df, output_path: str):
    logger.info(f"Writing output CSV to S3 path: {output_path}")
    try:
        (
            df.coalesce(1)
            .write.format("csv")
            .option("header", "true")
            .mode("overwrite")
            .save(output_path)
        )
        logger.info("Successfully loaded output data.")
    except Exception as err:
        logger.error(f"Failed to load CSV to output path {output_path}: {err}")
        raise


def run_pipeline(input_path: str, output_path: str):
    spark = create_spark_session()
    try:
        raw_df = extract_orders(spark, input_path)
        transformed_df = transform_customer_totals(raw_df)
        load_customer_totals(transformed_df, output_path)
        logger.info("ETL pipeline executed successfully.")
    except Exception as err:
        logger.critical(f"Pipeline failed: {err}")
        sys.exit(1)
    finally:
        spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PySpark Orders ETL Job")
    parser.add_argument("--input-path", required=True, help="S3 input path")
    parser.add_argument("--output-path", required=True, help="S3 output path")
    args = parser.parse_args()
    run_pipeline(args.input_path, args.output_path)
