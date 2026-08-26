import pytest
from pyspark.sql import SparkSession
from src.validator.schema_validator import SchemaValidator

@pytest.fixture(scope="module")
def spark():
    return SparkSession.builder.master("local[1]").appName("TestValidator").getOrCreate()

def test_schema_validator(spark):
    data = [
        ("0000100", "10", "20231001", "150.00"),  # Valid record
        (None, "20", "20231001", "200.00"),       # Invalid: Null Sales Document
        ("0000101", "10", "20231001", "-50.00")    # Invalid: Negative Net Value
    ]
    columns = ["VBELN", "POSNR", "ERDAT", "NETWR"]
    df = spark.createDataFrame(data, columns)
    
    valid_df, quarantine_df = SchemaValidator.validate_sales_data(df)
    
    assert valid_df.count() == 1
    assert quarantine_df.count() == 2
