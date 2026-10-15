-- Create raw staging table for daily CSV loads
CREATE TABLE IF NOT EXISTS orders_raw (
    order_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    order_date VARCHAR NOT NULL,
    amount FLOAT NOT NULL,
    currency VARCHAR,
    status VARCHAR NOT NULL,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Create target table for transformed orders
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    amount FLOAT NOT NULL,
    currency VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Create quarantine table for rejected records
CREATE TABLE IF NOT EXISTS quarantine (
    order_id INTEGER,
    customer_id INTEGER,
    order_date VARCHAR,
    amount FLOAT,
    currency VARCHAR,
    status VARCHAR,
    rejection_reason VARCHAR NOT NULL,
    rejected_at TIMESTAMP NOT NULL,
    source_file VARCHAR NOT NULL,
    quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Create pipeline execution metrics table
CREATE TABLE IF NOT EXISTS pipeline_execution_metrics (
    pipeline_name VARCHAR NOT NULL,
    execution_date VARCHAR,
    status VARCHAR NOT NULL,
    records_loaded INTEGER,
    records_rejected INTEGER,
    error_message VARCHAR,
    executed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Create index for common queries
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_status ON pipeline_execution_metrics(status, executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_quarantine_date ON quarantine(rejected_at DESC);
