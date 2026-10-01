# Daily Orders S3-to-Snowflake ELT Pipeline

This pipeline loads daily orders CSV files from AWS S3 into Snowflake using an ELT pattern. Raw data is staged in Snowflake and transformed using SQL, leveraging Snowflake's compute for scalability.

## How to run this

### 1. Prerequisites

- Python 3.9+
- AWS credentials configured (via environment variables, IAM role, or shared credentials file)
- Snowflake account with appropriate permissions
- `snowflake-connector-python` and `pandas` libraries (see step 2)

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
- `SNOWFLAKE_USER`: Snowflake username
- `SNOWFLAKE_PASSWORD`: Snowflake password
- `SNOWFLAKE_WAREHOUSE`: Warehouse name
- `SNOWFLAKE_DATABASE`: Database name
- `SNOWFLAKE_SCHEMA`: Schema name
- `S3_BUCKET`: S3 bucket containing orders CSV files
- `S3_PREFIX`: Prefix/folder in S3 where orders files are stored
- `AWS_REGION`: AWS region

Note: `.env.example` is committed with blank values to serve as a template. Real credentials go only in `.env`, which is excluded from version control by `.gitignore`.

### 4. Running the pipeline

```bash
python src/pipeline.py
```

Or with explicit date:

```bash
python src/pipeline.py --date 2024-01-15
```

For testing:

```bash
pytest tests/
```
