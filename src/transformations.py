import logging
from typing import Tuple
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, TimestampType, DateType

logger = logging.getLogger(__name__)

class SalesDataTransformer:
    """Validates, cleans, transforms, and splits valid vs bad SAP sales records."""
    
    @staticmethod
    def validate_and_split(df: DataFrame) -> Tuple[DataFrame, DataFrame]:
        """Separates malformed or missing key records into quarantine."""
        # Mandatory fields validation
        valid_condition = (
            F.col("sales_doc_num").isNotNull() &
            F.col("item_num").isNotNull() &
            F.col("create_date").isNotNull()
        )
        
        valid_df = df.filter(valid_condition)
        invalid_df = df.filter(~valid_condition).withColumn(
            "quarantine_reason", 
            F.lit("Missing mandatory keys (sales_doc_num, item_num, or create_date)")
        ).withColumn("quarantined_at", F.current_timestamp())
        
        return valid_df, invalid_df

    @staticmethod
    def transform(df: DataFrame) -> DataFrame:
        """Applies data domain transformations and enrichment."""
        transformed_df = df \
            .withColumn("sales_doc_num", F.trim(F.col("sales_doc_num"))) \
            .withColumn("item_num", F.col("item_num").cast("integer")) \
            .withColumn("material_num", F.ltrim(F.col("material_num"), "0")) \
            .withColumn("order_qty", F.coalesce(F.col("order_qty").cast(DoubleType()), F.lit(0.0))) \
            .withColumn("item_net_value", F.coalesce(F.col("item_net_value").cast(DoubleType()), F.lit(0.0))) \
            .withColumn("header_net_value", F.coalesce(F.col("header_net_value").cast(DoubleType()), F.lit(0.0))) \
            .withColumn("created_at", F.to_timestamp(F.col("create_date"), "yyyyMMdd")) \
            .withColumn("updated_at", F.coalesce(
                F.to_timestamp(F.col("update_date"), "yyyyMMdd"),
                F.to_timestamp(F.col("create_date"), "yyyyMMdd")
            )) \
            .withColumn("sales_year", F.year(F.col("created_at"))) \
            .withColumn("sales_month", F.month(F.col("created_at"))) \
            .withColumn("etl_processed_at", F.current_timestamp())
            
        return transformed_df
