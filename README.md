# S3 Aggregation ETL Pipeline

Production-ready batch ETL pipeline in Python to extract order data from AWS S3, perform customer-level aggregation, and write output back to S3 without modifying the source data.

## How to run this

1. Prerequisites
   - Python 3.10 or higher.
   - Access permissions to the AWS S3 target and source buckets.

2. Installing dependencies
   Execute:
   ```bash
   pip install pandas boto3 python-dotenv pytest moto
   ```

3. Configuring credentials
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Fill in real values in `.env` only - `.env.example` stays blank so it can be committed - and `.gitignore` already excludes `.env` from version control, so nothing further needs doing there.

4. Running it
   Execute the main entry point:
   ```bash
   python -m src.main
   ```
