"""ETL logic for order aggregation."""

import logging
from io import StringIO
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    raise ImportError("pandas is required. Install with: pip install pandas")

from s3_client import S3Client


class OrderAggregationETL:
    """ETL processor for order aggregation by customer_id."""

    REQUIRED_COLUMNS = {"order_id", "customer_id", "amount"}

    def __init__(self, s3_client: S3Client, logger: logging.Logger):
        """Initialize ETL processor."""
        self.s3_client = s3_client
        self.logger = logger

    def run(
        self,
        source_bucket: str,
        source_key: str,
        output_bucket: str,
        output_prefix: str,
        execution_id: str,
    ) -> dict:
        """
        Execute the ETL pipeline.

        Returns:
            Execution result dictionary with status, record counts, and output keys.
        """
        start_time = datetime.now()
        result = {
            "execution_id": execution_id,
            "start_time": start_time.isoformat(),
            "status": "failed",
            "total_records": 0,
            "aggregated_records": 0,
            "rejected_records": 0,
            "output_key": None,
            "rejection_key": None,
            "error": None,
        }

        try:
            # Step 1: Extract
            self.logger.info(f"Extracting from s3://{source_bucket}/{source_key}")
            csv_content = self.s3_client.get_object(source_bucket, source_key)
            df = pd.read_csv(StringIO(csv_content.decode("utf-8")))
            result["total_records"] = len(df)
            self.logger.info(f"Read {len(df)} records from source")

            # Step 2: Validate schema
            self.logger.info("Validating schema")
            df, rejected = self._validate_schema(df)
            self.logger.info(
                f"Schema validation: {len(df)} valid, {len(rejected)} rejected"
            )

            # Step 3: Validate data types and values
            self.logger.info("Validating data types and values")
            df, type_rejected = self._validate_data_types(df)
            rejected = pd.concat([rejected, type_rejected], ignore_index=True)
            result["rejected_records"] = len(rejected)
            self.logger.info(
                f"Data validation: {len(df)} valid, {len(type_rejected)} rejected"
            )

            # Step 4: Transform (aggregate)
            self.logger.info("Aggregating by customer_id")
            aggregated = self._aggregate(df)
            result["aggregated_records"] = len(aggregated)
            self.logger.info(f"Aggregation complete: {len(aggregated)} unique customers")

            # Step 5: Quality checks
            self.logger.info("Performing quality checks")
            quality_passed = self._quality_checks(df, aggregated)
            if not quality_passed:
                raise Exception("Quality checks failed")
            self.logger.info("Quality checks passed")

            # Step 6: Load
            self.logger.info("Loading aggregated data to S3")
            output_key = f"{output_prefix}/customer_totals_{execution_id}.csv"
            aggregated_csv = aggregated.to_csv(index=False)
            self.s3_client.put_object(output_bucket, output_key, aggregated_csv)
            result["output_key"] = output_key
            self.logger.info(f"Aggregated data written to s3://{output_bucket}/{output_key}")

            # Write rejected records if any
            if len(rejected) > 0:
                rejection_key = f"{output_prefix}/rejections_{execution_id}.csv"
                rejection_csv = rejected.to_csv(index=False)
                self.s3_client.put_object(output_bucket, rejection_key, rejection_csv)
                result["rejection_key"] = rejection_key
                self.logger.info(
                    f"Rejected records written to s3://{output_bucket}/{rejection_key}"
                )

            result["status"] = "success"

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self.logger.error(f"ETL execution failed: {str(e)}", exc_info=True)
            raise

        finally:
            result["end_time"] = datetime.now().isoformat()
            duration = (
                datetime.fromisoformat(result["end_time"])
                - datetime.fromisoformat(result["start_time"])
            ).total_seconds()
            result["duration_seconds"] = duration
            self.logger.info(f"Execution completed in {duration:.2f} seconds")

        return result

    def _validate_schema(self, df: pd.DataFrame) -> tuple:
        """
        Validate DataFrame schema against required columns.

        Returns:
            Tuple of (valid_df, rejected_df) with rejection reason column.
        """
        missing_columns = self.REQUIRED_COLUMNS - set(df.columns)
        if missing_columns:
            raise ValueError(
                f"Source CSV missing required columns: {missing_columns}"
            )

        # No schema rejections if columns exist; data validation happens next
        return df, pd.DataFrame()

    def _validate_data_types(self, df: pd.DataFrame) -> tuple:
        """
        Validate and convert data types. Reject rows with invalid data.

        Returns:
            Tuple of (valid_df, rejected_df).
        """
        rejected_rows = []
        valid_df = df.copy()
        valid_indices = []

        for idx, row in df.iterrows():
            rejection_reason = None

            # Validate customer_id is not null
            if pd.isna(row["customer_id"]) or str(row["customer_id"]).strip() == "":
                rejection_reason = "customer_id is null or empty"

            # Validate order_id is not null
            elif pd.isna(row["order_id"]) or str(row["order_id"]).strip() == "":
                rejection_reason = "order_id is null or empty"

            # Validate amount is numeric
            else:
                try:
                    float(row["amount"])
                except (ValueError, TypeError):
                    rejection_reason = f"amount '{row['amount']}' is not numeric"

            if rejection_reason:
                rejected_row = row.to_dict()
                rejected_row["rejection_reason"] = rejection_reason
                rejected_rows.append(rejected_row)
            else:
                valid_indices.append(idx)

        valid_df = df.loc[valid_indices].copy()
        valid_df["amount"] = valid_df["amount"].astype(float)

        rejected_df = pd.DataFrame(rejected_rows) if rejected_rows else pd.DataFrame()

        return valid_df, rejected_df

    def _aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate orders by customer_id.

        Returns:
            DataFrame with columns: customer_id, total_amount, order_count.
        """
        aggregated = (
            df.groupby("customer_id")
            .agg(
                total_amount=("amount", "sum"),
                order_count=("order_id", "count"),
            )
            .reset_index()
        )

        # Ensure numeric types and round to 2 decimal places for currency
        aggregated["total_amount"] = aggregated["total_amount"].round(2)
        aggregated["order_count"] = aggregated["order_count"].astype(int)

        return aggregated.sort_values("customer_id").reset_index(drop=True)

    def _quality_checks(self, source_df: pd.DataFrame, aggregated_df: pd.DataFrame) -> bool:
        """
        Perform quality checks to validate aggregation integrity.

        Checks:
        - Unique customer count matches
        - Total amount sum matches
        - No null values in output

        Returns:
            True if all checks pass, False otherwise.
        """
        # Check: aggregated customer count matches unique source customers
        unique_source_customers = source_df["customer_id"].nunique()
        aggregated_customers = len(aggregated_df)
        if unique_source_customers != aggregated_customers:
            self.logger.warning(
                f"Customer count mismatch: source {unique_source_customers}, "
                f"aggregated {aggregated_customers}"
            )
            return False

        # Check: total amount sum matches
        source_total = source_df["amount"].sum()
        aggregated_total = aggregated_df["total_amount"].sum()
        if abs(source_total - aggregated_total) > 0.01:  # Allow for rounding
            self.logger.warning(
                f"Total amount mismatch: source {source_total}, "
                f"aggregated {aggregated_total}"
            )
            return False

        # Check: no null values in output
        if aggregated_df.isnull().any().any():
            self.logger.warning("Null values found in aggregated output")
            return False

        self.logger.info(
            f"Quality checks passed: {aggregated_customers} customers, "
            f"total amount {aggregated_total:.2f}"
        )
        return True
