import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)

class WatermarkManager:
    """Manages persistent watermark state stored in AWS S3."""
    def __init__(self, spark: SparkSession, watermark_path: str, default_lookback_days: int = 30):
        self.spark = spark
        self.watermark_path = watermark_path
        self.default_lookback_days = default_lookback_days

    def get_last_watermark(self) -> str:
        """Reads the last processed timestamp watermark or returns default lookback."""
        try:
            sc = self.spark.sparkContext
            conf = sc._jsc.hadoopConfiguration()
            path = sc._gateway.jvm.org.apache.hadoop.fs.Path(self.watermark_path)
            fs = path.getFileSystem(conf)
            
            if fs.exists(path):
                stream = fs.open(path)
                reader = sc._gateway.jvm.java.io.BufferedReader(
                    sc._gateway.jvm.java.io.InputStreamReader(stream, "UTF-8")
                )
                lines = []
                line = reader.readLine()
                while line is not None:
                    lines.append(line)
                    line = reader.readLine()
                reader.close()
                data = json.loads("".join(lines))
                last_wm = data.get("last_updated_at")
                logger.info(f"Successfully retrieved high watermark: {last_wm}")
                return last_wm
        except Exception as e:
            logger.warning(f"Could not read watermark from {self.watermark_path}: {e}. Falling back to default.")
        
        default_wm = (datetime.utcnow() - timedelta(days=self.default_lookback_days)).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Using default fallback watermark: {default_wm}")
        return default_wm

    def update_watermark(self, new_watermark: str) -> None:
        """Persists updated high watermark back to S3."""
        payload = {
            "last_updated_at": new_watermark,
            "updated_timestamp_utc": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            sc = self.spark.sparkContext
            conf = sc._jsc.hadoopConfiguration()
            path = sc._gateway.jvm.org.apache.hadoop.fs.Path(self.watermark_path)
            fs = path.getFileSystem(conf)
            out = fs.create(path, True)
            out.write(json.dumps(payload).encode("utf-8"))
            out.close()
            logger.info(f"Successfully updated high watermark to: {new_watermark}")
        except Exception as e:
            logger.error(f"Failed to update watermark state at {self.watermark_path}: {e}")
            raise e
