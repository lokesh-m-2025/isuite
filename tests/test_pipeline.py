import pytest
import pandas as pd
from io import StringIO
from moto import mock_aws
import boto3
from src.config import PipelineConfig
from src.pipeline import validate_and_clean_data, transform_orders, run_pipeline


def test_validate_and_clean_data_valid():
    raw_data = """order_id,customer_id,amount
101,CUST_A,100.50
102,CUST_A,50.25
103,CUST_B,200.00
"""
    df = pd.read_csv(StringIO(raw_data))
    valid_df, invalid_df = validate_and_clean_data(df)
    assert len(valid_df) == 3
    assert len(invalid_df) == 0


def test_validate_and_clean_data_with_invalid_rows():
    raw_data = """order_id,customer_id,amount
101,CUST_A,100.50
102,,50.25
103,CUST_B,invalid_amount
104,CUST_C,-10.00
"""
    df = pd.read_csv(StringIO(raw_data))
    valid_df, invalid_df = validate_and_clean_data(df)
    assert len(valid_df) == 1
    assert len(invalid_df) == 3
    assert valid_df.iloc[0]["customer_id"] == "CUST_A"


def test_transform_orders():
    raw_data = """order_id,customer_id,amount
101,CUST_A,100.50
102,CUST_A,50.25
103,CUST_B,200.00
"""
    df = pd.read_csv(StringIO(raw_data))
    valid_df, _ = validate_and_clean_data(df)
    transformed = transform_orders(valid_df)

    assert len(transformed) == 2
    row_a = transformed[transformed["customer_id"] == "CUST_A"].iloc[0]
    assert row_a["total_amount"] == 150.75
    assert row_a["order_count"] == 2

    row_b = transformed[transformed["customer_id"] == "CUST_B"].iloc[0]
    assert row_b["total_amount"] == 200.00
    assert row_b["order_count"] == 1


@mock_aws
def test_full_pipeline_run():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="test-bucket")

    csv_content = "order_id,customer_id,amount\n1,C1,10.0\n2,C1,20.0\n3,C2,50.0\n"
    s3.put_object(Bucket="test-bucket", Key="input/orders.csv", Body=csv_content.encode("utf-8"))

    config = PipelineConfig(
        aws_region="us-east-1",
        s3_input_bucket="test-bucket",
        s3_input_key="input/orders.csv",
        s3_output_bucket="test-bucket",
        s3_output_key="output/customer_totals.csv"
    )

    metrics = run_pipeline(config, s3_client=s3)
    assert metrics["status"] == "SUCCESS"
    assert metrics["total_input_rows"] == 3
    assert metrics["valid_rows"] == 3
    assert metrics["output_customer_rows"] == 2

    # Verify input file was untouched
    source_obj = s3.get_object(Bucket="test-bucket", Key="input/orders.csv")
    assert source_obj["Body"].read().decode("utf-8") == csv_content

    # Verify output result
    output_obj = s3.get_object(Bucket="test-bucket", Key="output/customer_totals.csv")
    out_csv = output_obj["Body"].read().decode("utf-8")
    assert "customer_id,total_amount,order_count" in out_csv
    assert "C1,30.0,2" in out_csv
    assert "C2,50.0,1" in out_csv
