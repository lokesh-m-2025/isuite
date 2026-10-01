"""Data transformation logic executed within Snowflake."""

import logging
from datetime import date

from src.snowflake_client import SnowflakeConnection

logger = logging.getLogger(__name__)


class OrdersTransformer:
    """Transforms staged orders data and merges into production table."""

    def __init__(self, sf_conn: SnowflakeConnection):
        self.sf_conn = sf_conn

    def merge_orders(self, execution_date: date) -> None:
        """
        Merge staged orders into production table.
        Uses upsert pattern: insert new orders, update existing ones.
        """
        merge_query = f"""
            MERGE INTO ORDERS t
            USING (
                SELECT DISTINCT
                    ORDER_ID,
                    CUSTOMER_ID,
                    ORDER_DATE,
                    TOTAL_AMOUNT,
                    STATUS,
                    LOAD_TIMESTAMP
                FROM ORDERS_STAGING
                WHERE EXECUTION_DATE = '{execution_date}'
            ) s
            ON t.ORDER_ID = s.ORDER_ID
            WHEN MATCHED THEN
                UPDATE SET
                    CUSTOMER_ID = s.CUSTOMER_ID,
                    ORDER_DATE = s.ORDER_DATE,
                    TOTAL_AMOUNT = s.TOTAL_AMOUNT,
                    STATUS = s.STATUS,
                    UPDATED_AT = CURRENT_TIMESTAMP()
            WHEN NOT MATCHED THEN
                INSERT (ORDER_ID, CUSTOMER_ID, ORDER_DATE, TOTAL_AMOUNT, STATUS, CREATED_AT, UPDATED_AT)
                VALUES (s.ORDER_ID, s.CUSTOMER_ID, s.ORDER_DATE, s.TOTAL_AMOUNT, s.STATUS, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())
        """

        try:
            self.sf_conn.execute(merge_query)
            logger.info(f"Merged orders for {execution_date}")
        except Exception as e:
            logger.error(f"Error merging orders: {e}")
            raise

        # Clean up staging for this execution
        self.sf_conn.execute(
            f"DELETE FROM ORDERS_STAGING WHERE EXECUTION_DATE = '{execution_date}'"
        )
        logger.info(f"Cleaned up staging for {execution_date}")
