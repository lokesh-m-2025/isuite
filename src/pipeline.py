import io
import logging
from typing import Tuple, Dict, Any
import pandas as pd
from src.config import PipelineConfig
from src.s3_client import get_s3_client, read_csv_from_s3, write_csv_to_s3

logger = logging.getLogger(__name__)


def validate_and_clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    required_cols = {"order_id", "customer_id", "amount"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in input CSV: {missing}")

    df_clean = df.copy()
    df_clean["amount"] = pd.to_numeric(df_clean["amount"], errors="coerce")

    is_invalid = (
        df_clean["customer_id"].isna() |
        (df_clean["customer_id"].astype(str).str.strip() == "") |
        df_clean["amount"].isna() |
        (df_clean["amount"] < 0)
    )

    invalid_df = df_clean[is_invalid].copy()
    valid_df = df_clean[~is_invalid].copy()
    valid_df["customer_id"] = valid_df["customer_id"].astype(str).str.strip()

    logger.info(f"Validation complete: {len(valid_df)} valid rows, {len(invalid_df)} invalid rows.")
    return valid_df, invalid_df


def transform_orders(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["customer_id", "total_amount", "order_count"])

    aggregated = df.groupby("customer_id").agg(
        total_amount=("amount", "sum"),
        order_count=("order_id", "count")
    ).reset_index()

    aggregated["total_amount"] = aggregated["total_amount"].round(2)
    aggregated = aggregated.sort_values(by="customer_id").reset_index(drop=True)
    return aggregated


def run_pipeline(config: PipelineConfig, s3_client=None) -> Dict[str, Any]:
    logger.info("Starting ETL execution.")
    if s3_client is None:
        s3_client = get_s3_client(config)

    raw_csv = read_csv_from_s3(s3_client, config.s3_input_bucket, config.s3_input_key)
    input_df = pd.read_csv(io.StringIO(raw_csv))
    total_input_rows = len(input_df)

    valid_df, invalid_df = validate_and_clean_data(input_df)
    transformed_df = transform_orders(valid_df)

    output_buffer = io.StringIO()
    transformed_df.to_csv(output_buffer, index=False)

    write_csv_to_s3(
        s3_client,
        config.s3_output_bucket,
        config.s3_output_key,
        output_buffer.getvalue()
    )

    metrics = {
        "status": "SUCCESS",
        "total_input_rows": total_input_rows,
        "valid_rows": len(valid_df),
        "invalid_rows": len(invalid_df),
        "output_customer_rows": len(transformed_df)
    }
    logger.info(f"ETL execution completed successfully: {metrics}")
    return metrics
