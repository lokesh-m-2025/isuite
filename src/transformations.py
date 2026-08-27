from pyspark.sql import DataFrame
import pyspark.sql.functions as F

def filter_valid_orders(df: DataFrame) -> DataFrame:
    """Filters out malformed records missing customer_id or negative/null amounts."""
    return df.filter(
        F.col("customer_id").isNotNull() &
        (F.trim(F.col("customer_id")) != "") &
        F.col("amount").isNotNull() &
        (F.col("amount") >= 0)
    )

def aggregate_customer_totals(df: DataFrame) -> DataFrame:
    """Groups orders by customer_id and calculates total amount and order count."""
    valid_df = filter_valid_orders(df)
    return valid_df.groupBy("customer_id").agg(
        F.round(F.sum("amount"), 2).alias("total_amount"),
        F.count("order_id").alias("order_count")
    ).orderBy(F.col("total_amount").desc())
