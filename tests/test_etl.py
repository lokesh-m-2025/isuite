import io
import boto3
import pandas as pd
import pytest
from moto import mock_aws
from src.config import Config
from src.etl import extract, transform, load, run_pipeline, parse_s3_uri


def test_parse_s3_uri():
    bucket, key = parse_s3_uri("s3://my-bucket/path/to/file.csv")
    assert bucket == "my-bucket"
    assert key == "path/to/file.csv"


def test_transform():
    raw_data = {
        "order_id": [1, 2, 3, 4],
        "customer_id": [101, 101, 102, None],
        "amount": [25.50, 74.50, 150.00, 50.00]
    }
    df = pd.DataFrame(raw_data)
    result = transform(df)
    assert len(result) == 2
    cust_101 = result[result["customer_id"] == 101].iloc[0]
    assert cust_101["total_amount"] == 100.00
    assert cust_101["order_count"] == 2


@mock_aws
def test_full_pipeline():
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket_name = "ignitho-development-bucket"
    s3.create_bucket(Bucket=bucket_name)

    sample_csv = "order_id,customer_id,amount\n1,C100,10.0\n2,C100,20.0\n3,C200,15.5\n"
    s3.put_object(Bucket=bucket_name, Key="input/sample-orders.csv", Body=sample_csv)

    cfg = Config(
        aws_region="us-east-1",
        source_s3_uri=f"s3://{bucket_name}/input/sample-orders.csv",
        target_s3_uri=f"s3://{bucket_name}/output/customer_totals_3.csv"
    )
    run_pipeline(cfg)

    res = s3.get_object(Bucket=bucket_name, Key="output/customer_totals_3.csv")
    out_df = pd.read_csv(io.BytesIO(res["Body"].read()))
    assert len(out_df) == 2
    assert set(out_df.columns) == {"customer_id", "total_amount", "order_count"}
