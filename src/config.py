import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class SnowflakeConfig:
    """Snowflake connection configuration."""
    account: str
    user: str
    password: str
    database: str
    schema: str
    warehouse: str

    @classmethod
    def from_env(cls) -> "SnowflakeConfig":
        """Load configuration from environment variables."""
        required_keys = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD",
                         "SNOWFLAKE_DATABASE", "SNOWFLAKE_SCHEMA", "SNOWFLAKE_WAREHOUSE"]
        missing = [k for k in required_keys if not os.getenv(k)]
        if missing:
            raise ValueError(f"Missing required Snowflake config: {', '.join(missing)}")

        return cls(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE")
        )


@dataclass
class PipelineConfig:
    """Pipeline execution configuration."""
    input_source: str
    csv_filename: str
    snowflake: SnowflakeConfig

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Load pipeline configuration from environment variables."""
        input_source = os.getenv("INPUT_SOURCE")
        csv_filename = os.getenv("CSV_FILENAME")

        if not input_source:
            raise ValueError("Missing INPUT_SOURCE (s3://... or /local/path)")
        if not csv_filename:
            raise ValueError("Missing CSV_FILENAME")

        return cls(
            input_source=input_source,
            csv_filename=csv_filename,
            snowflake=SnowflakeConfig.from_env()
        )
