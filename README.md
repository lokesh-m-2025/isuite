# CSV to Snowflake ETL Pipeline

Daily batch pipeline that loads orders CSV from S3 into Snowflake.

## How to Run This

### 1. Prerequisites

- Python 3.9 or later
- AWS credentials configured (via `~/.aws/credentials`, environment variables, or IAM role)
- Snowflake account with:
  - A warehouse
  - A database
  - A schema
  - A role with permissions to create tables
  - Tables pre-created:
    - `{schema}.orders_raw` (raw staging table)
    - `{schema}.orders` (target table)
    - `{schema}.quarantine` (rejected records table)
    - `{schema}.pipeline_execution_metrics` (audit table)

### 2. Installing Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configuring Credentials

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in all required values:
   - `AWS_REGION`: AWS region where S3 bucket is located
   - `S3_BUCKET`: Name of S3 bucket containing daily CSV files
   - `S3_KEY`: S3 object key (path) to the CSV file to load
   - `SNOWFLAKE_ACCOUNT`: Snowflake account identifier
   - `SNOWFLAKE_USER`: Snowflake user for pipeline
   - `SNOWFLAKE_PASSWORD`: Snowflake password (use a service account)
   - `SNOWFLAKE_WAREHOUSE`: Snowflake warehouse name
   - `SNOWFLAKE_DATABASE`: Target database
   - `SNOWFLAKE_SCHEMA`: Target schema
   - `SNOWFLAKE_ROLE`: Snowflake role for pipeline execution

3. `.env` is excluded from version control by `.gitignore`, so secrets are safe.

### 4. Running the Pipeline

```bash
python -m src.pipeline
```

The pipeline will:
1. Read the CSV from S3
2. Validate schema and data quality
3. Quarantine invalid records with reasons
4. Load valid records into the raw staging table
5. Execute transformation SQL to populate the target table
6. Record execution metrics

Exit code:
- `0` on success
- `1` on failure (errors are logged, metrics are recorded)

## Running Tests

```bash
pytest tests/ -v
```

Tests include:
- Schema validation (column presence, types, nullability)
- Data quality checks (duplicates)
- Integration tests (S3 read, Snowflake write with mocking)

## Deployment

### AWS Lambda

1. Package the application:
   ```bash
   zip -r function.zip src/ config/ sql/ .
   ```

2. Create a Lambda function with:
   - Runtime: Python 3.11
   - Handler: `src.pipeline.run_pipeline`
   - IAM role with:
     - `s3:GetObject` permission on the bucket and key
     - No Snowflake-specific IAM permissions (Snowflake auth via user/password)
   - Environment variables from `.env`

3. Schedule with EventBridge (CloudWatch Events) for daily execution.

### AWS Step Functions / Apache Airflow

Use the pipeline as a single step:

- Input: `{"s3_key": "path/to/daily-orders.csv"}` (override `S3_KEY` from environment)
- Output: Execution status and metrics

## Monitoring

Pipeline execution is tracked in `{schema}.pipeline_execution_metrics`:

```sql
SELECT * FROM pipeline_execution_metrics
ORDER BY executed_at DESC
LIMIT 10;
```

Columns:
- `pipeline_name`: Pipeline identifier
- `execution_date`: Date of execution
- `status`: "SUCCESS" or "FAILED"
- `records_loaded`: Number of records inserted into target
- `records_rejected`: Number of records sent to quarantine
- `error_message`: Error details (if status = "FAILED")
- `executed_at`: Timestamp of execution

Rejected records are available in `{schema}.quarantine` for review and recovery.

## Architecture

**Pattern**: ELT (Extract-Load-Transform)

Data flows:
1. **S3 CSV** → Read with pandas, validate schema and quality
2. **Schema & Quality Validation** → Separate valid and invalid rows
3. **Valid Rows** → Load to Snowflake raw staging table (`orders_raw`)
4. **Invalid Rows** → Load to Snowflake quarantine table with rejection reason
5. **Raw Staging** → Transform with SQL (dedup, type conversion, business logic)
6. **Target Table** → `orders` table ready for analysis
7. **Execution Metrics** → Log pipeline run details for monitoring

Full load each day: staging and target tables are truncated before insert.

## Configuration Files

- `config/schema.json`: Expected CSV columns, types, nullability
- `sql/transform.sql`: SQL transformations from raw to target
- `.env`: Runtime credentials and paths (never commit)
- `requirements.txt`: Python dependencies
