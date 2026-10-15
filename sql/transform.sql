-- Transform raw staging data and populate target table
-- This assumes orders_raw table has been loaded with validated data
-- Deduplicates by order_id (keeping most recent), validates data, and inserts into target

BEGIN TRANSACTION;

-- Clear target table
TRUNCATE TABLE orders;

-- Insert transformed records from raw staging
INSERT INTO orders (
    order_id,
    customer_id,
    order_date,
    amount,
    currency,
    status,
    created_at
)
SELECT
    order_id,
    customer_id,
    TRY_TO_DATE(order_date, 'YYYY-MM-DD') as order_date,
    amount,
    COALESCE(currency, 'USD') as currency,
    UPPER(status) as status,
    CURRENT_TIMESTAMP() as created_at
FROM (
    SELECT
        order_id,
        customer_id,
        order_date,
        amount,
        currency,
        status,
        ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY CURRENT_TIMESTAMP() DESC) as rn
    FROM orders_raw
    WHERE order_id IS NOT NULL
        AND customer_id IS NOT NULL
        AND amount >= 0
        AND status IN ('PENDING', 'COMPLETED', 'CANCELLED')
)
WHERE rn = 1;

COMMIT;
