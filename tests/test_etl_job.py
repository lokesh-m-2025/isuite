"""Unit tests for PySpark orders ETL pipeline functions."""
import pytest
from pyspark.sql import SparkSession
from src.etl_job import ORDERS_SCHEMA, transform_customer_totals


@pytest.fixture(scope="module")
def spark():
    session = (
        SparkSession.builder.master("local[2]")
        .appName("ETLUnitTests")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
    yield session
    session.stop()


def test_transform_customer_totals(spark):
    data = [
        ("ord1", "cust101", "2026-03-01", 100.50),
        ("ord2", "cust101", "2026-03-02", 49.50),
        ("ord3", "cust102", "2026-03-01", 200.00),
        ("ord4", None, "2026-03-01", 50.00),
        ("ord5", "cust103", "2026-03-01", -10.00),
    ]

    df = spark.createDataFrame(data, schema=ORDERS_SCHEMA)
    result_df = transform_customer_totals(df)
    results = {row["customer_id"]: (row["total_amount"], row["order_count"]) for row in result_df.collect()}

    assert "cust101" in results
    assert results["cust101"] == (150.00, 2)
    assert results["cust102"] == (200.00, 1)
    assert "cust103" not in results
    assert None not in results
