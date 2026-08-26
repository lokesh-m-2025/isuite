from pyspark.sql import SparkSession
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_spark_session(app_name: str) -> SparkSession:
    logger.info("Initializing PySpark Session with S3A dynamic partitioning configurations...")
    spark = (
        SparkSession.builder
        .appName(app_name)
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.DefaultAWSCredentialsProviderChain")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark
