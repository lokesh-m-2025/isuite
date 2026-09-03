import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class PipelineConfig(BaseModel):
    aws_region: str = Field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))
    aws_access_key_id: Optional[str] = Field(default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID"))
    aws_secret_access_key: Optional[str] = Field(default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY"))
    aws_session_token: Optional[str] = Field(default_factory=lambda: os.getenv("AWS_SESSION_TOKEN"))
    s3_input_bucket: str = Field(default_factory=lambda: os.getenv("S3_INPUT_BUCKET", "your-bucket"))
    s3_input_key: str = Field(default_factory=lambda: os.getenv("S3_INPUT_KEY", "input/orders.csv"))
    s3_output_bucket: str = Field(default_factory=lambda: os.getenv("S3_OUTPUT_BUCKET", "your-bucket"))
    s3_output_key: str = Field(default_factory=lambda: os.getenv("S3_OUTPUT_KEY", "output/customer_totals.csv"))

    @property
    def source_s3_path(self) -> str:
        return f"s3://{self.s3_input_bucket}/{self.s3_input_key}"

    @property
    def target_s3_path(self) -> str:
        return f"s3://{self.s3_output_bucket}/{self.s3_output_key}"
