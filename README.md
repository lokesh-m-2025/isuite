# S3 CSV to S3 Orders ETL Pipeline

This is a production-grade ETL pipeline that extracts order data from an S3 CSV file, validates and transforms it by aggregating order amounts and counts per customer, and loads the results to a separate S3 location.

## Architecture Overview

The pipeline follows a layered ETL approach:

1. **Ingestion**: Read CSV from source S3 bucket with processing state tracking
2. **Validation**: Schema validation, type checking, null handling
3. **Quarantine**: Separate malformed records into a rejected bucket
4. **Transformation**: Group by customer_id, calculate aggregates
5. **Quality Checks**: Output validation and reconciliation
6. **Loading**: Write results to output S3 bucket
7. **Monitoring**: CloudWatch Logs with execution metrics

## How to Run This

### 1. Prerequisites

- Python 3.9 or later
- AWS CLI configured with appropriate credentials (via IAM role or environment variables)
- Access to S3 bucket with read access to `input/` and write access to `output/` and `rejected/` paths
- CloudWatch Logs permissions for logging

### 2. Installing Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configuring Credentials

Copy `.env.example` to `.env` and fill in the real configuration values:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:
- `AWS_REGION`: The AWS region where your S3 bucket is located (e.g., us-east-1)
- `S3_BUCKET_NAME`: The S3 bucket name without s3:// prefix
- `LOG_GROUP_NAME`: CloudWatch Log Group name for pipeline logs
- `LOG_STREAM_NAME`: CloudWatch Log Stream name for this execution

The `.gitignore` file already excludes `.env` from version control, so your credentials are safe. `.env.example` remains in the repository with blank values for reference.

### 4. Running the Pipeline

Execute the main pipeline:

```bash
python src/main.py
```

This will:
- Extract orders from `s3://your-bucket/input/orders.csv`
- Validate and transform the data
- Write customer aggregates to `s3://your-bucket/output/customer_totals.csv`
- Write rejected records to `s3://your-bucket/rejected/customer_totals_rejected_TIMESTAMP.csv`
- Log all metrics and errors to CloudWatch

### Running Tests

```bash
pytest tests/ -v
```

## Configuration

All configuration is externalized in the `.env` file. See `.env.example` for available options.

## Output Files

- **Success output**: `s3://your-bucket/output/customer_totals.csv`
  - Columns: customer_id, total_amount, order_count
  - One row per unique customer

- **Rejected records**: `s3://your-bucket/rejected/customer_totals_rejected_TIMESTAMP.csv`
  - Columns: original_record, rejection_reason, timestamp
  - Contains all malformed or invalid records

## Idempotency

The pipeline uses a processing marker file to track execution state:
- Location: `s3://your-bucket/.pipeline_markers/customer_totals_last_run.txt`
- Re-running the same execution on the same date will detect this marker and skip processing
- To force a re-run, manually delete the marker file

## Monitoring

All execution metrics are logged to CloudWatch:
- Pipeline execution start and end times
- Records processed, accepted, and rejected
- Processing errors with detailed reasons
- Data quality violations

Query logs with:
```bash
aws logs tail <log-group-name> --follow
```

## Troubleshooting

- **"Access Denied" errors**: Verify IAM role has s3:GetObject, s3:PutObject, and logs:CreateLogStream permissions
- **"CSV parse errors"**: Check that source CSV is valid UTF-8 and uses consistent delimiters; rejected records are saved for inspection
- **"No records processed"**: Verify source file exists at s3://your-bucket/input/orders.csv
- **"Duplicate processing"**: Check for processing marker file; delete if you want to force re-run

## Support

For pipeline failures, check CloudWatch Logs for detailed error messages and rejected record details.
