-- Initialize Snowflake tables for ETL pipeline
-- Run this once in the target database/schema

-- Target table (orders)
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    order_date DATE NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (order_id)
);

-- Staging table (raw CSV data before validation)
CREATE TABLE IF NOT EXISTS orders_staging (
    order_id VARCHAR(50),
    customer_id VARCHAR(50),
    order_date VARCHAR(50),
    amount VARCHAR(50),
    status VARCHAR(50)
);

-- Quarantine table (malformed records)
CREATE TABLE IF NOT EXISTS orders_quarantine (
    row_number INT,
    raw_data VARCHAR(4000),
    error_reason VARCHAR(500),
    quarantined_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Pipeline execution metadata
CREATE TABLE IF NOT EXISTS pipeline_execution_log (
    execution_id VARCHAR(50) PRIMARY KEY,
    source_file VARCHAR(500),
    valid_count INT,
    malformed_count INT,
    status VARCHAR(20),
    execution_timestamp TIMESTAMP_NTZ
);
