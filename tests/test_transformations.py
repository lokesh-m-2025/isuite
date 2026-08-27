import pytest
from pyspark.sql import SparkSession
from src.schemas import ORDERS_SCHEMA
from src.transformations import aggregate_customer_totals, filter_valid_orders

@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder \
        .master("local[2]") \
        .appName("UnitTests") \
        .getOrCreate()

def test_filter_valid_orders(spark):
    data = [
        ("101", "CUST_A", 150.00, "2023-10-01"),
        ("102", None, 50.00, "2023-10-01"),
        ("103", "CUST_B", -25.00, "2023-10-02"),
        ("104", "   ", 75.00, "2023-10-02")
    ]
    df = spark.createDataFrame(data, ORDERS_SCHEMA)
    filtered = filter_valid_orders(df)
    records = filtered.collect()

    assert len(records) == 1
    assert records[0]["customer_id"] == "CUST_A"
    assert records[0]["amount"] == 150.00

def test_aggregate_customer_totals(spark):
    data = [
        ("101", "CUST_1", 100.50, "2023-10-01"),
        ("102", "CUST_1", 200.25, "2023-10-02"),
        ("103", "CUST_2", 50.00, "2023-10-03")
    ]
    df = spark.createDataFrame(data, ORDERS_SCHEMA)
    aggregated = aggregate_customer_totals(df)
    results = aggregated.collect()

    assert len(results) == 2
    cust1 = next(r for r in results if r["customer_id"] == "CUST_1")
    assert cust1["total_amount"] == 300.75
    assert cust1["order_count"] == 2
