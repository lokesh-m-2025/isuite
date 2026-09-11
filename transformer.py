import pandas as pd
import logging


class OrderTransformer:
    """Transforms raw order data into customer-level aggregates."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def aggregate_by_customer(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group orders by customer_id and aggregate metrics.
        
        Output columns:
        - customer_id: unique customer identifier
        - total_amount: sum of all order amounts for the customer
        - order_count: number of orders for the customer
        
        Args:
            df: DataFrame with columns [customer_id, amount]
        
        Returns:
            Aggregated DataFrame
        """
        if df.empty:
            self.logger.warning("Input DataFrame is empty; returning empty result")
            return pd.DataFrame(
                columns=["customer_id", "total_amount", "order_count"]
            )
        
        aggregated = (
            df.groupby("customer_id", as_index=False)
            .agg({
                "amount": ["sum", "count"]
            })
        )
        
        # Flatten multi-level columns
        aggregated.columns = ["customer_id", "total_amount", "order_count"]
        
        # Round total_amount to 2 decimal places for currency
        aggregated["total_amount"] = aggregated["total_amount"].round(2)
        
        # Convert order_count to int
        aggregated["order_count"] = aggregated["order_count"].astype(int)
        
        # Sort by customer_id for deterministic output
        aggregated = aggregated.sort_values("customer_id").reset_index(drop=True)
        
        self.logger.info(
            f"Aggregated {len(df)} orders into {len(aggregated)} "
            f"unique customers"
        )
        return aggregated
