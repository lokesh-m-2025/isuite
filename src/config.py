import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PipelineConfig:
    """Loads and validates pipeline configuration from environment variables."""
    def __init__(self):
        self.app_name: str = os.getenv("APP_NAME", "SAP_Sales_ETL_Pipeline")
        self.env: str = os.getenv("ENVIRONMENT", "production")
        
        # SAP Connection
        self.sap_jdbc_url: str = os.getenv("SAP_JDBC_URL", "")
        self.sap_db_user: str = os.getenv("SAP_DB_USER", "")
        self.sap_db_password: str = os.getenv("SAP_DB_PASSWORD", "")
        self.sap_driver: str = os.getenv("SAP_JDBC_DRIVER", "com.sap.db.jdbc.Driver")
        self.sap_table_header: str = os.getenv("SAP_TABLE_HEADER", "VBAK")
        self.sap_table_item: str = os.getenv("SAP_TABLE_ITEM", "VBAP")
        
        # Target S3 Config
        self.s3_target_path: str = os.getenv("S3_TARGET_PATH", "s3a://data-lake-curated/sap/sales/")
        self.s3_quarantine_path: str = os.getenv("S3_QUARANTINE_PATH", "s3a://data-lake-quarantine/sap/sales/")
        self.s3_watermark_path: str = os.getenv("S3_WATERMARK_PATH", "s3a://data-lake-state/sap/sales_watermark.json")
        
        # Operational Config
        self.fetch_size: int = int(os.getenv("JDBC_FETCH_SIZE", "50000"))
        self.num_partitions: int = int(os.getenv("SPARK_NUM_PARTITIONS", "20"))
        self.default_lookback_days: int = int(os.getenv("DEFAULT_LOOKBACK_DAYS", "30"))
        
        self._validate()

    def _validate(self) -> None:
        missing = []
        if not self.sap_jdbc_url:
            missing.append("SAP_JDBC_URL")
        if not self.s3_target_path:
            missing.append("S3_TARGET_PATH")
        if missing:
            raise ValueError(f"Missing required configuration variables: {', '.join(missing)}")

    def get_spark_jdbc_properties(self) -> Dict[str, str]:
        props = {
            "driver": self.sap_driver,
            "fetchsize": str(self.fetch_size)
        }
        if self.sap_db_user:
            props["user"] = self.sap_db_user
        if self.sap_db_password:
            props["password"] = self.sap_db_password
        return props
