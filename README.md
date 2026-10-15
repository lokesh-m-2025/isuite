# S3 CSV to Snowflake ETL Pipeline

Daily load of orders CSV from S3 into Snowflake with validation, error handling, and idempotent execution.

## How to run this

### 1. Prerequisites

- Python 3.9+
- AWS credentials configured (via IAM role, `~/.aws/credentials`, or environment variables)
- Access to AWS Secrets Manager containing Snowflake credentials
- Snowflake account with appropriate role and warehouse
- S3 bucket with daily CSV files

### 2. Installing dependencies

```bash
pip install -r requirements.txt
```

### 3. Configuring credentials

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and fill in real values:
- `SNOWFLAKE_ACCOUNT`: Your Snowflake account identifier
- `SNOWFLAKE_USER`: Snowflake user for pipeline execution
- `SNOWFLAKE_PASSWORD`: Password for Snowflake user
- `SNOWFLAKE_DATABASE`: Target database name
- `SNOWFLAKE_SCHEMA`: Target schema name
- `SNOWFLAKE_WAREHOUSE`: Warehouse to use for compute
- `SNOWFLAKE_ROLE`: Role for pipeline execution
- `S3_BUCKET`: S3 bucket containing CSV files
- `S3_KEY_PREFIX`: Path prefix to CSV files (e.g., `orders/daily/`)
- `AWS_REGION`: AWS region (e.g., `us-east-1`)

`.env` is excluded from version control by `.gitignore`, so credentials are not committed.

### 4. Running the pipeline

```bash
python src/main.py
```

The script will:
1. Discover the latest CSV in S3
2. Validate schema and format
3. Load raw data into Snowflake staging table
4. Check for malformed records (route to quarantine table)
5. Replace target table with valid data
6. Record execution metrics
7. Exit with status code 0 on success, non-zero on failure

For scheduled execution (e.g., daily via cron or AWS EventBridge), wrap the command in your orchestration tool and monitor exit code and logs.

## Project structure

```
.
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── src/
│   ├── main.py                 # Entry point
│   ├── config.py               # Configuration loader
│   ├── s3_client.py            # S3 operations
│   ├── snowflake_client.py     # Snowflake operations
│   └── csv_validator.py        # CSV schema validation
├── sql/
│   ├── init.sql                # Create staging and quarantine tables
│   ├── merge_valid_records.sql # Merge valid records into target
│   └── record_execution.sql    # Record pipeline execution metadata
└── tests/
    ├── test_csv_validator.py
    ├── test_snowflake_client.py
    └── test_main.py
```
