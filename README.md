# Orders ETL Pipeline

Production-grade batch ETL pipeline that reads order data from S3, aggregates by customer, validates data quality, and writes aggregated results back to S3.

## How to run this

### 1. Prerequisites

Python 3.8 or later, and the following:

- AWS account with S3 access (via IAM role on EC2/Lambda or environment variables)
- Boto3 CLI configured (for local development) or IAM role attached (for EC2/Lambda)
- Read access to `s3://ignitho-development-bucket/input/`
- Write access to `s3://ignitho-development-bucket/output/`

### 2. Installing dependencies

```bash
pip install -r requirements.txt
```

### 3. Configuring credentials

Copy `.env.example` to `.env` and fill in real values:

```bash
cp .env.example .env
```

Edit `.env` with actual values. Do not commit `.env` — it is already listed in `.gitignore`.

Alternatively, set environment variables directly:

```bash
export SOURCE_BUCKET="ignitho-development-bucket"
export SOURCE_KEY="input/sample-orders.csv"
export TARGET_BUCKET="ignitho-development-bucket"
export TARGET_KEY="output/customer_totals.csv"
export AWS_REGION="us-east-1"
```

On EC2 or Lambda, attach an IAM role with S3 permissions instead of using credentials.

### 4. Running it

```bash
python etl_pipeline.py
```

Pipeline logs appear in:
- `etl_pipeline.log` (local file)
- Stdout (console)
- CloudWatch (if enabled in logger.py)

## Input format

CSV with headers `customer_id` and `amount`. Example:

```csv
customer_id,amount
C001,100.50
C001,75.25
C002,200.00
```

## Output format

CSV with headers `customer_id`, `total_amount`, and `order_count`. Example:

```csv
customer_id,total_amount,order_count
C001,175.75,2
C002,200.00,1
```

## Data quality

Records are validated for:
- Non-null customer_id
- Non-null amount
- Numeric amount value

Invalid records are logged and written to a separate file but do not halt processing. Valid records are aggregated and written to the output file.

## Error handling

The pipeline handles:
- Missing source file
- S3 connection errors
- CSV parsing errors
- Invalid data values
- S3 write failures

All errors are logged with timestamps and execution ID for debugging.

## Deployment

### EC2

1. Attach IAM role with S3 permissions
2. Set environment variables or `.env` file
3. Run: `python etl_pipeline.py`
4. Optionally schedule with cron or CloudWatch Events

### AWS Lambda

1. Create Lambda function (Python 3.8+)
2. Attach IAM role with S3 permissions
3. Set environment variables via Lambda console
4. Upload code as ZIP (including dependencies)
5. Set handler to `etl_pipeline.main`
6. Optional: trigger from S3 or schedule with EventBridge

## Testing

Run unit and integration tests:

```bash
python -m pytest tests/
```

Or with unittest:

```bash
python -m unittest discover tests
```
