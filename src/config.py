import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class SnowflakeConfig:
    account: str
    user: str
    password: str
    database: str
    schema: str
    warehouse: str
    role: str

    @classmethod
    def from_env(cls) -> "SnowflakeConfig":
        return cls(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            role=os.getenv("SNOWFLAKE_ROLE"),
        )


@dataclass
class S3Config:
    bucket: str
    key_prefix: str
    region: str

    @classmethod
    def from_env(cls) -> "S3Config":
        return cls(
            bucket=os.getenv("S3_BUCKET"),
            key_prefix=os.getenv("S3_KEY_PREFIX"),
            region=os.getenv("AWS_REGION"),
        )


@dataclass
class PipelineConfig:
    snowflake: SnowflakeConfig
    s3: S3Config
    target_table: str = "orders"
    staging_table: str = "orders_staging"
    quarantine_table: str = "orders_quarantine"
    metadata_table: str = "pipeline_execution_log"

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        return cls(
            snowflake=SnowflakeConfig.from_env(),
            s3=S3Config.from_env(),
        )
