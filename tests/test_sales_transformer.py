import pytest
from pyspark.sql import SparkSession
from src.transformer.sales_transformer import SalesTransformer

@pytest.fixture(scope="module")
def spark():
    return SparkSession.builder.master("local[1]").appName("TestTransformer").getOrCreate()

def test_sales_transformation(spark):
    data = [
        ("001", "10", "20231001", "20231002", "100.00", "USD", "CUST1", "MAT1"),
        ("001", "10", "20231001", "20231005", "120.00", "USD", "CUST1", "MAT1")  # Newer update
    ]
    columns = ["VBELN", "POSNR", "ERDAT", "AEDAT", "NETWR", "WAERK", "KUNNR", "MATNR"]
    df = spark.createDataFrame(data, columns)
    
    result_df = SalesTransformer.transform(df)
    
    assert result_df.count() == 1
    row = result_df.first()
    assert row["net_amount"] == 120.00
    assert row["year"] == 2023
    assert row["month"] == "10"
    assert row["day"] == "01"
