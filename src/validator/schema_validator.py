from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from typing import Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SchemaValidator:
    @staticmethod
    def validate_sales_data(df: DataFrame) -> Tuple[DataFrame, DataFrame]:
        logger.info("Performing data validation and quality checks...")
        
        validation_condition = (
            F.col("VBELN").isNotNull() &
            F.col("POSNR").isNotNull() &
            (F.col("NETWR").cast("double") >= 0.0) &
            F.col("ERDAT").isNotNull()
        )
        
        valid_df = df.filter(validation_condition)
        quarantine_df = df.filter(~validation_condition).withColumn(
            "quarantine_reason",
            F.concat_ws(
                "; ",
                F.when(F.col("VBELN").isNull(), "Null Sales Document").otherwise(F.lit(None)),
                F.when(F.col("POSNR").isNull(), "Null Item Number").otherwise(F.lit(None)),
                F.when(F.col("NETWR").cast("double") < 0.0, "Negative Net Value").otherwise(F.lit(None)),
                F.when(F.col("ERDAT").isNull(), "Null Creation Date").otherwise(F.lit(None))
            )
        ).withColumn("rejected_at", F.current_timestamp())
        
        return valid_df, quarantine_df
