import io
import logging
import pandas as pd
import boto3
from botocore.exceptions import ClientError
from src.config import Config

logger = logging.getLogger(__name__)

class CustomerTotalsETL:
    def __init__(self, config: Config = Config):
        self.config = config
        session_kwargs = {"region_name": config.AWS_REGION}
        if config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY:
            session_kwargs["aws_access_key_id"] = config.AWS_ACCESS_KEY_ID
            session_kwargs["aws_secret_access_key"] = config.AWS_SECRET_ACCESS_KEY
        self.s3_client = boto3.client("s3", **session_kwargs)

    def extract(self) -> pd.DataFrame:
        bucket, key = self.config.parse_s3_uri(self.config.S3_SOURCE_URI)
        logger.info("Extracting file from S3 bucket: %s, key: %s", bucket, key)
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            body = response["Body"].read()
            df = pd.read_csv(io.BytesIO(body))
            logger.info("Successfully extracted %d rows from S3 source.", len(df))
            return df
        except ClientError as e:
            logger.error("Failed to extract S3 object: %s", e)
            raise

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            logger.warning("Extracted DataFrame is empty.")
            return pd.DataFrame(columns=["customer_id", "total_amount", "order_count"])
        
        # Standardize amount column name if variant exists
        if "amount" not in df.columns and "order_amount" in df.columns:
            df = df.rename(columns={"order_amount": "amount"})
            
        if "customer_id" not in df.columns or "amount" not in df.columns:
            raise KeyError("Input dataset missing required columns: 'customer_id' or 'amount'")

        # Data quality checks & cleaning
        initial_len = len(df)
        df_clean = df.dropna(subset=["customer_id", "amount"]).copy()
        df_clean["amount"] = pd.to_numeric(df_clean["amount"], errors="coerce")
        df_clean = df_clean.dropna(subset=["amount"])
        
        dropped_count = initial_len - len(df_clean)
        if dropped_count > 0:
            logger.warning("Dropped %d invalid or null records during transformation.", dropped_count)

        # Aggregate total amount and count of orders per customer
        grouped = df_clean.groupby("customer_id").agg(
            total_amount=("amount", "sum"),
            order_count=("amount", "count")
        ).reset_index()

        # Round amounts for precision
        grouped["total_amount"] = grouped["total_amount"].round(2)
        logger.info("Transformation complete. Generated summary for %d distinct customers.", len(grouped))
        return grouped

    def load(self, df: pd.DataFrame) -> None:
        bucket, key = self.config.parse_s3_uri(self.config.S3_TARGET_URI)
        logger.info("Loading aggregated output to S3 bucket: %s, key: %s", bucket, key)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=csv_buffer.getvalue().encode("utf-8"),
                ContentType="text/csv"
            )
            logger.info("Successfully loaded %d records to target S3 location.", len(df))
        except ClientError as e:
            logger.error("Failed to write output to S3: %s", e)
            raise

    def run(self) -> None:
        logger.info("Starting Customer Totals ETL process.")
        raw_df = self.extract()
        transformed_df = self.transform(raw_df)
        self.load(transformed_df)
        logger.info("ETL process completed successfully.")
