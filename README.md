# Daily Orders CSV to Snowflake ELT Pipeline

Production-grade batch ETL pipeline that loads daily orders from CSV (S3 or local) into Snowflake with comprehensive validation, error handling, and observability.

## Architecture

- **Ingestion**: Read CSV file from S3 or local filesystem.
- **Validation**: Schema validation, type checking, null handling, duplicate detection.
- **Raw Layer**: Load validated records into Snowflake staging table (RAW_ORDERS).
- **Transformation**: Execute SQL transformations in Snowflake to produce clean ORDERS table.
- **Quality Checks**: Record count reconciliation, null checks, business rule validation.
- **Error Handling**: Rejected records written to REJECTED_ORDERS with failure reasons.
- **Monitoring**: Execution metadata and metrics logged to PIPELINE_EXECUTIONS.

## How to Run This

### 1. Prerequisites

- Python 3.10 or later
- Snowflake account and permissions to create/write tables
- S3 bucket access (if using S3; local file mode requires filesystem access)
- AWS credentials configured (if using S3)

### 2. Installing Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configuring Credentials

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and populate all values:
- `SNOWFLAKE_ACCOUNT`: Snowflake account identifier (e.g., `xy12345.us-east-1`)
- `SNOWFLAKE_USER`: Snowflake user
- `SNOWFLAKE_PASSWORD`: Snowflake password
- `SNOWFLAKE_DATABASE`: Target database name
- `SNOWFLAKE_SCHEMA`: Target schema name
- `SNOWFLAKE_WAREHOUSE`: Warehouse to use
- `AWS_ACCESS_KEY_ID`: AWS credentials (leave blank for IAM role)
- `AWS_SECRET_ACCESS_KEY`: AWS credentials (leave blank for IAM role)
- `INPUT_SOURCE`: Either `s3://bucket-name/prefix/` or `/local/path/to/csv/`
- `CSV_FILENAME`: Name of CSV file to load (e.g., `orders.csv`)

**Important**: `.env` is excluded from version control by `.gitignore`. Never commit real credentials. `.env.example` remains blank and can be safely committed.

### 4. Running the Pipeline

```bash
python src/pipeline.py
```

On success, prints execution summary with record counts and metrics. On failure, prints error and exits with non-zero code.

## Testing

```bash
pytest tests/ -v
```

## Production Deployment

Schedule `python src/pipeline.py` as a daily cron job or via AWS Lambda/Airflow:

```bash
# Cron example (daily at 02:00 UTC)
0 2 * * * cd /opt/pipeline && python src/pipeline.py >> /var/log/orders_pipeline.log 2>&1
```

Ensure `.env` is present on execution host and readable only by pipeline user.
