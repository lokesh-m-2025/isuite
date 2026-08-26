import pytest
from pyspark.sql import SparkSession
from src.transformations import SalesDataTransformer

@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder \
        .master("local[2]") \
        .appName("test_sap_transformations") \
        .getOrCreate()

def test_validate_and_split_quarantine(spark):
    data = [
        ("0010001234", "000010", "20231015"),
        (None, "000020", "20231015"),  # Invalid: Null doc num
        ("0010001235", None, "20231015")  # Invalid: Null item num
    ]
    columns = ["sales_doc_num", "item_num", "create_date"]
    df = spark.createDataFrame(data, columns)
    
    valid_df, invalid_df = SalesDataTransformer.validate_and_split(df)
    
    assert valid_df.count() == 1
    assert invalid_df.count() == 2

def test_transformation_padding_and_types(spark):
    data = [("0010001234", "000010", "000000000012345678", "10.50", "100.00", "20231015", "20231016")]
    columns = ["sales_doc_num", "item_num", "material_num", "order_qty", "item_net_value", "create_date", "update_date"]
    df = spark.createDataFrame(data, columns)
    
    transformed_df = SalesDataTransformer.transform(df)
    row = transformed_df.first()
    
    assert row["material_num"] == "12345678"
    assert row["order_qty"] == 10.50
    assert row["sales_year"] == 2023
    assert row["sales_month"] == 10
