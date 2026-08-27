import logging
from pyspark.sql import SparkSession
from src.config import Config

def get_logger(name: str = "CustomerTotalsETL") -> logging.Logger:
    """Initializes standardized logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def init_spark_session(config: Config) -> SparkSession:
    """Constructs SparkSession configured for AWS S3 access."""
    builder = SparkSession.builder \
        .appName("CustomerTotalsETL") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")

    if config.aws_access_key_id and config.aws_secret_access_key:
        builder = builder \
            .config("spark.hadoop.fs.s3a.access.key", config.aws_access_key_id) \
            .config("spark.hadoop.fs.s3a.secret.key", config.aws_secret_access_key) \
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        if config.aws_session_token:
            builder = builder \
                .config("spark.hadoop.fs.s3a.session.token", config.aws_session_token) \
                .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.TemporaryAWSCredentialsProvider")

    return builder.getOrCreate()
