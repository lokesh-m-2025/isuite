import logging
import pandas as pd

logger = logging.getLogger(__name__)

class OrderTransformer:
    REQUIRED_COLUMNS = ["customer_id", "amount"]

    def validate_schema(self, df: pd.DataFrame) -> None:
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Source CSV missing required columns: {missing_cols}")

    def transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
        self.validate_schema(df)
        total_raw_records = len(df)
        logger.info(f"Starting transformation on {total_raw_records} raw records.")

        # Drop missing customer_id
        valid_df = df.dropna(subset=["customer_id"]).copy()
        dropped_missing_customer = total_raw_records - len(valid_df)

        # Coerce numeric amount
        valid_df["amount"] = pd.to_numeric(valid_df["amount"], errors="coerce")
        before_amount_clean = len(valid_df)
        valid_df = valid_df.dropna(subset=["amount"])
        dropped_invalid_amount = before_amount_clean - len(valid_df)

        # Ensure customer_id type
        valid_df["customer_id"] = valid_df["customer_id"].astype(str).str.strip()
        valid_df = valid_df[valid_df["customer_id"] != ""]

        # Aggregation
        aggregated_df = (
            valid_df.groupby("customer_id", as_index=False)
            .agg(
                total_amount=("amount", "sum"),
                order_count=("amount", "count")
            )
        )

        aggregated_df["total_amount"] = aggregated_df["total_amount"].round(2)
        aggregated_df = aggregated_df.sort_values(by="customer_id").reset_index(drop=True)

        metrics = {
            "raw_records": total_raw_records,
            "valid_records": len(valid_df),
            "dropped_missing_customer": dropped_missing_customer,
            "dropped_invalid_amount": dropped_invalid_amount,
            "transformed_customers": len(aggregated_df)
        }

        logger.info(f"Transformation complete: {metrics}")
        return aggregated_df, metrics
