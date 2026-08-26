from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SalesTransformer:
    @staticmethod
    def transform(df: DataFrame) -> DataFrame:
        logger.info("Applying transformation logic: deduplication, date partitioning, and field standardization...")
        
        transformed_df = df.withColumn("sales_doc_id", F.col("VBELN")) \
            .withColumn("item_number", F.col("POSNR").cast("integer")) \
            .withColumn("created_date", F.to_date(F.col("ERDAT"), "yyyyMMdd")) \
            .withColumn("net_amount", F.col("NETWR").cast("decimal(15,2)")) \
            .withColumn("currency", F.col("WAERK")) \
            .withColumn("customer_id", F.col("KUNNR")) \
            .withColumn("material_id", F.col("MATNR")) \
            .withColumn("updated_timestamp", F.coalesce(F.to_timestamp(F.col("AEDAT"), "yyyyMMdd"), F.to_timestamp(F.col("ERDAT"), "yyyyMMdd"))) \
            .withColumn("processed_at", F.current_timestamp())
        
        # Deduplicate using Window function based on key (sales_doc_id, item_number)
        window_spec = Window.partitionBy("sales_doc_id", "item_number").orderBy(F.col("updated_timestamp").desc())
        deduped_df = transformed_df.withColumn("row_num", F.row_number().over(window_spec)) \
            .filter(F.col("row_num") == 1) \
            .drop("row_num")
            
        # Extract Partition Columns
        final_df = deduped_df \
            .withColumn("year", F.year(F.col("created_date"))) \
            .withColumn("month", F.format_string("%02d", F.month(F.col("created_date")))) \
            .withColumn("day", F.format_string("%02d", F.dayofmonth(F.col("created_date"))))
            
        return final_df
