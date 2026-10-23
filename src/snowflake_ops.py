import snowflake.connector
from snowflake.connector import DictCursor
from datetime import datetime
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


def create_connection(config):
    """Create Snowflake connection."""
    try:
        conn = snowflake.connector.connect(
            account=config.account,
            user=config.user,
            password=config.password,
            database=config.database,
            schema=config.schema,
            warehouse=config.warehouse
        )
        logger.info("Connected to Snowflake")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to Snowflake: {str(e)}")
        raise


def execute_query(conn, query: str, params: Optional[list] = None) -> list[dict]:
    """Execute query and return results as list of dicts."""
    try:
        cursor = conn.cursor(DictCursor)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        raise


def create_staging_table(conn) -> None:
    """Create raw staging table if not exists."""
    query = """
    CREATE TABLE IF NOT EXISTS RAW_ORDERS (
        order_id VARCHAR(255),
        customer_id VARCHAR(255),
        order_date VARCHAR(255),
        amount VARIANT,
        status VARCHAR(255),
        _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    )
    """
    execute_query(conn, query)
    logger.info("Ensured RAW_ORDERS staging table exists")


def create_rejected_table(conn) -> None:
    """Create rejected records table if not exists."""
    query = """
    CREATE TABLE IF NOT EXISTS REJECTED_ORDERS (
        order_id VARCHAR(255),
        customer_id VARCHAR(255),
        order_date VARCHAR(255),
        amount VARCHAR(255),
        status VARCHAR(255),
        rejection_reason VARCHAR(1024),
        _rejected_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    )
    """
    execute_query(conn, query)
    logger.info("Ensured REJECTED_ORDERS table exists")


def create_target_table(conn) -> None:
    """Create target ORDERS table if not exists."""
    query = """
    CREATE TABLE IF NOT EXISTS ORDERS (
        order_id VARCHAR(255) PRIMARY KEY,
        customer_id VARCHAR(255) NOT NULL,
        order_date DATE NOT NULL,
        amount DECIMAL(18, 2) NOT NULL,
        status VARCHAR(50) NOT NULL,
        _transformed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
        _batch_date DATE DEFAULT CURRENT_DATE()
    )
    """
    execute_query(conn, query)
    logger.info("Ensured ORDERS target table exists")


def create_pipeline_log_table(conn) -> None:
    """Create pipeline execution log table if not exists."""
    query = """
    CREATE TABLE IF NOT EXISTS PIPELINE_EXECUTIONS (
        execution_id VARCHAR(255) PRIMARY KEY,
        pipeline_name VARCHAR(255),
        status VARCHAR(50),
        records_read INT,
        records_valid INT,
        records_rejected INT,
        start_time TIMESTAMP_NTZ,
        end_time TIMESTAMP_NTZ,
        error_message VARCHAR(2048),
        created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    )
    """
    execute_query(conn, query)
    logger.info("Ensured PIPELINE_EXECUTIONS log table exists")


def insert_raw_records(conn, records: list[dict]) -> int:
    """Insert records into RAW_ORDERS staging table. Returns count inserted."""
    if not records:
        return 0

    try:
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO RAW_ORDERS (order_id, customer_id, order_date, amount, status)
        VALUES (%s, %s, %s, %s, %s)
        """
        for record in records:
            cursor.execute(insert_query, (
                record.get("order_id"),
                record.get("customer_id"),
                record.get("order_date"),
                record.get("amount"),
                record.get("status")
            ))
        cursor.close()
        conn.commit()
        logger.info(f"Inserted {len(records)} records into RAW_ORDERS")
        return len(records)
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to insert raw records: {str(e)}")
        raise


def insert_rejected_records(conn, rejected_records: list[tuple[dict, str]]) -> int:
    """Insert rejected records into REJECTED_ORDERS table. Returns count inserted."""
    if not rejected_records:
        return 0

    try:
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO REJECTED_ORDERS (order_id, customer_id, order_date, amount, status, rejection_reason)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        for record, error in rejected_records:
            cursor.execute(insert_query, (
                record.get("order_id"),
                record.get("customer_id"),
                record.get("order_date"),
                str(record.get("amount")) if record.get("amount") is not None else None,
                record.get("status"),
                error
            ))
        cursor.close()
        conn.commit()
        logger.info(f"Inserted {len(rejected_records)} rejected records into REJECTED_ORDERS")
        return len(rejected_records)
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to insert rejected records: {str(e)}")
        raise


def transform_raw_to_target(conn) -> int:
    """
    Transform and load from RAW_ORDERS to ORDERS table.
    Returns count of records inserted/updated.
    """
    try:
        cursor = conn.cursor()
        merge_query = """
        MERGE INTO ORDERS t
        USING (
            SELECT
                order_id,
                customer_id,
                TO_DATE(order_date) as order_date,
                CAST(amount AS DECIMAL(18, 2)) as amount,
                LOWER(status) as status
            FROM RAW_ORDERS
            WHERE order_date IS NOT NULL
              AND amount IS NOT NULL
              AND order_id IS NOT NULL
        ) s
        ON t.order_id = s.order_id
        WHEN MATCHED THEN
            UPDATE SET
                t.customer_id = s.customer_id,
                t.order_date = s.order_date,
                t.amount = s.amount,
                t.status = s.status,
                t._transformed_at = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN
            INSERT (order_id, customer_id, order_date, amount, status)
            VALUES (s.order_id, s.customer_id, s.order_date, s.amount, s.status)
        """
        cursor.execute(merge_query)
        rows_affected = cursor.rowcount
        cursor.close()
        conn.commit()
        logger.info(f"Transformed {rows_affected} records to ORDERS table")
        return rows_affected
    except Exception as e:
        conn.rollback()
        logger.error(f"Transformation failed: {str(e)}")
        raise


def get_row_count(conn, table_name: str) -> int:
    """Get row count from table."""
    results = execute_query(conn, f"SELECT COUNT(*) as cnt FROM {table_name}")
    return results[0]["CNT"] if results else 0


def log_execution(conn, execution_id: str, pipeline_name: str, status: str,
                  records_read: int, records_valid: int, records_rejected: int,
                  start_time: datetime, end_time: datetime, error_message: Optional[str] = None) -> None:
    """Log pipeline execution to PIPELINE_EXECUTIONS table."""
    try:
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO PIPELINE_EXECUTIONS
        (execution_id, pipeline_name, status, records_read, records_valid, records_rejected,
         start_time, end_time, error_message)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            execution_id,
            pipeline_name,
            status,
            records_read,
            records_valid,
            records_rejected,
            start_time,
            end_time,
            error_message
        ))
        cursor.close()
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to log execution: {str(e)}")
