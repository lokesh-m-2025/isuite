import snowflake.connector
import logging
from typing import List, Dict, Any
from datetime import datetime
from src.config import SnowflakeConfig, PipelineConfig

logger = logging.getLogger(__name__)


class SnowflakeClient:
    def __init__(self, config: SnowflakeConfig):
        self.config = config
        self.conn = None

    def connect(self) -> None:
        """Establish connection to Snowflake."""
        try:
            self.conn = snowflake.connector.connect(
                user=self.config.user,
                password=self.config.password,
                account=self.config.account,
                warehouse=self.config.warehouse,
                database=self.config.database,
                schema=self.config.schema,
                role=self.config.role,
            )
            logger.info("Connected to Snowflake")
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            raise

    def disconnect(self) -> None:
        """Close Snowflake connection."""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from Snowflake")

    def execute(self, query: str, params: List[Any] = None) -> None:
        """Execute a query without returning results."""
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            logger.debug(f"Executed: {query[:100]}...")
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            cursor.close()

    def fetch_one(self, query: str, params: List[Any] = None) -> Any:
        """Execute query and return first row."""
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            cursor.close()

    def fetch_all(self, query: str, params: List[Any] = None) -> List[Any]:
        """Execute query and return all rows."""
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            cursor.close()

    def insert_records(
        self, table: str, records: List[Dict[str, Any]]
    ) -> int:
        """Batch insert records into table. Returns row count inserted."""
        if not records:
            logger.warning(f"No records to insert into {table}")
            return 0

        cursor = self.conn.cursor()
        try:
            columns = list(records[0].keys())
            col_str = ", ".join(columns)
            placeholders = ", ".join(["?" for _ in columns])
            query = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})"

            rows_inserted = 0
            for record in records:
                values = [record[col] for col in columns]
                cursor.execute(query, values)
                rows_inserted += 1

            self.conn.commit()
            logger.info(f"Inserted {rows_inserted} records into {table}")
            return rows_inserted

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Batch insert failed: {e}")
            raise
        finally:
            cursor.close()

    def truncate_table(self, table: str) -> None:
        """Truncate a table."""
        try:
            self.execute(f"TRUNCATE TABLE {table}")
            logger.info(f"Truncated {table}")
        except Exception as e:
            logger.error(f"Failed to truncate {table}: {e}")
            raise

    def record_execution(
        self,
        metadata_table: str,
        execution_id: str,
        source_file: str,
        valid_count: int,
        malformed_count: int,
        status: str,
    ) -> None:
        """Record pipeline execution metadata."""
        try:
            query = f"""
                INSERT INTO {metadata_table}
                (execution_id, source_file, valid_count, malformed_count, status, execution_timestamp)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP())
            """
            self.execute(
                query,
                [execution_id, source_file, valid_count, malformed_count, status],
            )
            logger.info(f"Recorded execution {execution_id}")
        except Exception as e:
            logger.error(f"Failed to record execution: {e}")
            raise
