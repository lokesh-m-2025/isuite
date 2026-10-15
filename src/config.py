import os
from pathlib import Path


class Config:
    """Pipeline configuration loaded from environment variables."""

    def __init__(self):
        # AWS configuration
        self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
        self.S3_BUCKET = os.getenv("S3_BUCKET")
        self.S3_KEY = os.getenv("S3_KEY")

        if not self.S3_BUCKET or not self.S3_KEY:
            raise ValueError("S3_BUCKET and S3_KEY environment variables are required")

        # Snowflake configuration
        self.SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
        self.SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
        self.SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
        self.SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
        self.SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
        self.SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")
        self.SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE")

        required_sf = [
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_USER",
            "SNOWFLAKE_PASSWORD",
            "SNOWFLAKE_WAREHOUSE",
            "SNOWFLAKE_DATABASE",
            "SNOWFLAKE_SCHEMA",
            "SNOWFLAKE_ROLE",
        ]
        missing = [v for v in required_sf if not os.getenv(v)]
        if missing:
            raise ValueError(f"Missing Snowflake configuration: {', '.join(missing)}")

        # Pipeline configuration
        self.PIPELINE_NAME = os.getenv("PIPELINE_NAME", "csv_to_snowflake")
        self.EXECUTION_DATE = os.getenv("EXECUTION_DATE", "")
        self.RAW_TABLE = os.getenv("RAW_TABLE", "orders_raw")
        self.TARGET_TABLE = os.getenv("TARGET_TABLE", "orders")
        self.QUARANTINE_TABLE = os.getenv("QUARANTINE_TABLE", "quarantine")

        # Path to schema definition and transformation SQL
        config_dir = Path(__file__).parent
        self.SCHEMA_PATH = os.getenv(
            "SCHEMA_PATH", str(config_dir.parent / "config" / "schema.json")
        )
        self.TRANSFORMATION_SQL_PATH = os.getenv(
            "TRANSFORMATION_SQL_PATH", str(config_dir.parent / "sql" / "transform.sql")
        )

        if not Path(self.SCHEMA_PATH).exists():
            raise ValueError(f"Schema definition file not found: {self.SCHEMA_PATH}")
        if not Path(self.TRANSFORMATION_SQL_PATH).exists():
            raise ValueError(f"Transformation SQL file not found: {self.TRANSFORMATION_SQL_PATH}")
