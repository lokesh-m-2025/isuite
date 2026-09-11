import logging
import sys
from io import StringIO
from datetime import datetime
from typing import Tuple, Dict, Any

import boto3
import pandas as pd
from botocore.exceptions import ClientError, NoCredentialsError

from config import Config
from logger import setup_logger
from validator import SchemaValidator, DataValidator
from transformer import OrderTransformer


class OrdersETLPipeline:
    """Production-grade ETL pipeline for customer order aggregation."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger(config.log_file_path)
        self.s3_client = boto3.client("s3", region_name=config.aws_region)
        self.execution_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.metrics = {
            "execution_id": self.execution_id,
            "source_rows": 0,
            "valid_rows": 0,
            "invalid_rows": 0,
            "output_rows": 0,
            "status": "PENDING",
            "error": None,
        }

    def read_source_csv(self) -> Tuple[pd.DataFrame, list]:
        """Read CSV from S3 with error handling.
        
        Returns:
            Tuple of (DataFrame, list of error messages)
        """
        errors = []
        try:
            self.logger.info(
                f"Reading source file: s3://{self.config.source_bucket}/"
                f"{self.config.source_key}"
            )
            obj = self.s3_client.get_object(
                Bucket=self.config.source_bucket, Key=self.config.source_key
            )
            df = pd.read_csv(obj["Body"])
            self.metrics["source_rows"] = len(df)
            self.logger.info(f"Successfully read {len(df)} rows from source")
            return df, errors
        except FileNotFoundError as e:
            msg = f"Source file not found: {e}"
            self.logger.error(msg)
            errors.append(msg)
            return pd.DataFrame(), errors
        except ClientError as e:
            msg = f"S3 client error reading source: {e}"
            self.logger.error(msg)
            errors.append(msg)
            return pd.DataFrame(), errors
        except pd.errors.ParserError as e:
            msg = f"CSV parsing error: {e}"
            self.logger.error(msg)
            errors.append(msg)
            return pd.DataFrame(), errors

    def validate_and_clean(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Validate schema and data quality; separate valid from invalid rows.
        
        Returns:
            Tuple of (valid DataFrame, invalid DataFrame with error reasons)
        """
        schema_validator = SchemaValidator(self.config.required_columns)
        schema_errors = schema_validator.validate(df)
        if schema_errors:
            for error in schema_errors:
                self.logger.error(f"Schema validation error: {error}")

        data_validator = DataValidator()
        valid_df, invalid_df = data_validator.validate_and_separate(df)
        
        self.metrics["valid_rows"] = len(valid_df)
        self.metrics["invalid_rows"] = len(invalid_df)
        
        if len(invalid_df) > 0:
            self.logger.warning(
                f"Found {len(invalid_df)} invalid rows; storing separately"
            )
            self._store_invalid_records(invalid_df)
        
        return valid_df, invalid_df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply transformations: group by customer_id, aggregate."""
        transformer = OrderTransformer()
        aggregated_df = transformer.aggregate_by_customer(df)
        self.metrics["output_rows"] = len(aggregated_df)
        self.logger.info(
            f"Transformation complete: {self.metrics['output_rows']} "
            f"unique customers"
        )
        return aggregated_df

    def write_output_csv(self, df: pd.DataFrame) -> bool:
        """Write aggregated results to S3 as CSV.
        
        Returns:
            True if write succeeded, False otherwise
        """
        try:
            if df.empty:
                self.logger.warning("Output DataFrame is empty; writing empty file")
            
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
            
            self.logger.info(
                f"Writing output to s3://{self.config.target_bucket}/"
                f"{self.config.target_key}"
            )
            self.s3_client.put_object(
                Bucket=self.config.target_bucket,
                Key=self.config.target_key,
                Body=csv_content,
                ContentType="text/csv",
            )
            self.logger.info("Successfully wrote output file to S3")
            return True
        except ClientError as e:
            msg = f"S3 client error writing output: {e}"
            self.logger.error(msg)
            self.metrics["error"] = msg
            return False

    def _store_invalid_records(self, invalid_df: pd.DataFrame) -> None:
        """Store invalid records for debugging (optional)."""
        try:
            invalid_key = (
                self.config.target_key.replace(
                    ".csv", f"_invalid_{self.execution_id}.csv"
                )
            )
            csv_buffer = StringIO()
            invalid_df.to_csv(csv_buffer, index=False)
            self.s3_client.put_object(
                Bucket=self.config.target_bucket,
                Key=invalid_key,
                Body=csv_buffer.getvalue(),
                ContentType="text/csv",
            )
            self.logger.info(f"Stored invalid records to s3://{self.config.target_bucket}/{invalid_key}")
        except ClientError as e:
            self.logger.warning(f"Could not store invalid records: {e}")

    def run(self) -> Dict[str, Any]:
        """Execute the full ETL pipeline.
        
        Returns:
            Dictionary with execution metrics and status
        """
        start_time = datetime.utcnow()
        self.logger.info(f"Pipeline execution started: {self.execution_id}")
        
        try:
            # Extract
            df_source, read_errors = self.read_source_csv()
            if read_errors or df_source.empty:
                raise RuntimeError("Failed to read source file")
            
            # Validate
            df_valid, df_invalid = self.validate_and_clean(df_source)
            if df_valid.empty:
                raise RuntimeError(
                    f"No valid records after validation; "
                    f"{len(df_invalid)} records failed"
                )
            
            # Transform
            df_aggregated = self.transform(df_valid)
            
            # Load
            write_success = self.write_output_csv(df_aggregated)
            if not write_success:
                raise RuntimeError("Failed to write output file to S3")
            
            self.metrics["status"] = "SUCCESS"
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            self.logger.info(
                f"Pipeline execution completed successfully in {elapsed:.2f}s. "
                f"Processed: {self.metrics['source_rows']} source rows, "
                f"Valid: {self.metrics['valid_rows']}, "
                f"Invalid: {self.metrics['invalid_rows']}, "
                f"Output: {self.metrics['output_rows']}"
            )
            return self.metrics
        
        except NoCredentialsError as e:
            msg = f"AWS credentials not found: {e}"
            self.logger.error(msg)
            self.metrics["status"] = "FAILED"
            self.metrics["error"] = msg
            return self.metrics
        
        except Exception as e:
            msg = f"Pipeline execution failed: {str(e)}"
            self.logger.error(msg, exc_info=True)
            self.metrics["status"] = "FAILED"
            self.metrics["error"] = msg
            return self.metrics


def main() -> int:
    """Entry point for the ETL pipeline."""
    try:
        config = Config.from_environment()
        pipeline = OrdersETLPipeline(config)
        metrics = pipeline.run()
        
        if metrics["status"] == "SUCCESS":
            return 0
        else:
            return 1
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
