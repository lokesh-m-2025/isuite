from pyspark.sql.types import DoubleType, StringType, StructField, StructType

ORDERS_SCHEMA = StructType([
    StructField("order_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("order_date", StringType(), True)
])
