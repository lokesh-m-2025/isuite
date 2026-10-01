"""Snowflake connection and data loading utilities."""

import json
import logging
from typing import Any, List, Optional, Tuple

import snowflake.connector
from snowflake.connector.errors import ProgrammingError

logger = logging.getLogger(__name__)


class SnowflakeConnection:
    """Manages Snowflake connection and operations."""

    def __init__(
        self,
        account: str,
        user: str,
        password: str,
        warehouse: str,
        database: str,
        schema: str,
    ):
        self.account = account
        self.user = user
        self.password = password
        self.warehouse = warehouse
        self.database = database
        self.schema = schema
        self.conn = None
        self.cursor = None

    def connect(self) -> None:
        """Establish connection to Snowflake."""
        try:
            self.conn = snowflake.connector.connect(
                account=self.account,
                user=self.user,
                password=self.password,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema,
            )
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to Snowflake: {self.account}.{self.database}.{self.schema}")
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            raise

    def close(self) -> None:
        """Close Snowflake connection."""
        if self.conn:
            self.conn.close()
            logger.info("Closed Snowflake connection")

    def execute(self, query: str) -> None:
        """Execute a SQL query without returning results."""
        if not self.cursor:
            raise RuntimeError("Not connected to Snowflake")
        try:
            self.cursor.execute(query)
            logger.debug(f"Executed: {query[:100]}...")
        except ProgrammingError as e:
            logger.error(f"SQL error: {e}")
            raise
        except Exception as e:
            logger.error(f"Execution error: {e}")
            raise

    def fetch_one(self, query: str) -> Optional[Tuple]:
        """Execute query and return single row."""
        if not self.cursor:
            raise RuntimeError("Not connected to Snowflake")
        try:
            self.cursor.execute(query)
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            raise

    def fetch_all(self, query: str) -> List[Tuple]:
        """Execute query and return all rows."""
        if not self.cursor:
            raise RuntimeError("Not connected to Snowflake")
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            raise

    def load_staging(
        self, table: str, records: List[dict], execution_date: Any
    ) -> None:
        """Load validated records into staging table."""
        if not records:
            logger.info("No records to load")
            return

        try:
            for record in records:
                query = f"""
                    INSERT INTO {table}
                    (ORDER_ID, CUSTOMER_ID, ORDER_DATE, TOTAL_AMOUNT, STATUS, RAW_RECORD, LOAD_TIMESTAMP, EXECUTION_DATE)
                    VALUES (
                        '{record['order_id']}',
                        '{record['customer_id']}',
                        '{record['order_date']}',
                        {record['total_amount']},
                        '{record['status']}',
                        PARSE_JSON('{json.dumps(record)}'),
                        CURRENT_TIMESTAMP(),
                        '{execution_date}'
                    )
                """
                self.execute(query)

            logger.info(f"Loaded {len(records)} records into {table}")
        except Exception as e:
            logger.error(f"Error loading staging: {e}")
            raise

    def load_rejected_records(
        self, table: str, records: List[dict], execution_date: Any
    ) -> None:
        """Load rejected records with error details."""
        if not records:
            return

        try:
            for record in records:
                query = f"""
                    INSERT INTO {table}
                    (REJECTED_ID, RAW_RECORD, ERROR_MESSAGE, REJECTED_AT, EXECUTION_DATE)
                    VALUES (
                        '{record['rejected_id']}',
                        '{record['raw_record'].replace("'", "''")}',
                        '{record['error_message'].replace("'", "''")}',
                        CURRENT_TIMESTAMP(),
                        '{execution_date}'
                    )
                """
                self.execute(query)

            logger.info(f"Loaded {len(records)} rejected records into {table}")
        except Exception as e:
            logger.error(f"Error loading rejected records: {e}")
            raise
