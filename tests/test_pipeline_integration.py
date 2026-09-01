import io
import pytest
import pandas as pd
from moto import mock_aws
import boto3
from src.config import PipelineConfig
from src.extractor import S3Extractor
from src.transformer import OrderTransformer
from src.loader import S3Loader

@pytest.fixture
def aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

@mock_aws
def test_full_etl_flow(aws_credentials):
    s3_client = boto3.client("s3", region_name="us-east-1")
    bucket_name = "ignitho-development-bucket"
    s3_client.create_bucket(Bucket=bucket_name)
    
    input_csv = "order_id,customer_id,amount\n1,C101,10.0\n2,C101,20.0\n3,C102,15.5\n"
    s3_client.put_object(
        Bucket=bucket_name,
        Key="input/sample-orders.csv",
        Body=input_csv.encode("utf-8")
    )
    
    config = PipelineConfig(
        aws_region="us-east-1",
        source_s3_uri=f"s3://{bucket_name}/input/sample-orders.csv",
        target_s3_uri=f"s3://{bucket_name}/output/customer_totals.csv"
    )
    
    extractor = S3Extractor(config, s3_client=s3_client)
    transformer = OrderTransformer()
    loader = S3Loader(config, s3_client=s3_client)
    
    raw_df = extractor.extract_csv(config.source_s3_uri)
    transformed_df, metrics = transformer.transform(raw_df)
    loader.load_csv(transformed_df, config.target_s3_uri)
    
    # Verify output in target S3
    response = s3_client.get_object(Bucket=bucket_name, Key="output/customer_totals.csv")
    output_df = pd.read_csv(io.BytesIO(response["Body"].read()))
    
    assert len(output_df) == 2
    assert list(output_df.columns) == ["customer_id", "total_amount", "order_count"]
    c101 = output_df[output_df["customer_id"] == "C101"].iloc[0]
    assert c101["total_amount"] == 30.0
    assert c101["order_count"] == 2
