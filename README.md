# Order Aggregation ETL Pipeline

Batch ETL pipeline that reads orders from S3, aggregates by customer_id, and writes customer totals to S3.

## How to Run This

### 1. Prerequisites

- Python 3.9+
- AWS credentials configured (via environment variables, IAM role, or `~/.aws/credentials`)
- Access to the specified S3 bucket and paths

### 2. Installing Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configuring Credentials

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `AWS_REGION`: AWS region (e.g., `us-east-1`)
- `SOURCE_BUCKET`: S3 bucket name
- `SOURCE_KEY`: Path to source CSV
- `OUTPUT_BUCKET`: S3 bucket name for output
- `OUTPUT_PREFIX`: S3 prefix for output files

**Important:** `.env` is excluded from version control by `.gitignore`. Store real values only in `.env`, never in `.env.example`.

### 4. Running It

```bash
python src/pipeline.py
```

The script will:
1. Read the source CSV from S3
2. Validate schema and data types
3. Quarantine malformed records to `rejections_<timestamp>.csv`
4. Aggregate valid records by customer_id
5. Write results to `customer_totals_<timestamp>.csv`
6. Log execution metadata to `execution_log_<timestamp>.json`

## Output Files

- `customer_totals_<timestamp>.csv`: Aggregated results with columns `customer_id`, `total_amount`, `order_count`
- `rejections_<timestamp>.csv`: Rejected records with reason (if any records failed validation)
- `execution_log_<timestamp>.json`: Pipeline execution metadata
