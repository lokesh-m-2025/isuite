# Order ETL Pipeline

This repository contains a production‑grade Python ETL pipeline that extracts daily order CSV files from an AWS S3 bucket, validates and cleans the data, and loads incremental records into a Snowflake ORDERS table.

## How to run this

1. **Prerequisites**
   - Python 3.9+
   - `pip` package manager

2. **Installing dependencies**
   ```bash
   pip install boto3 snowflake-connector-python python-dotenv
   ```

3. **Configuring credentials**
   ```bash
   cp .env.example .env
   # Edit .env and fill in the real values
   ```
   The `.env` file is ignored by Git (`.gitignore`), so your secrets stay out of version control.

4. **Running it**
   ```bash
   python -m src.etl
   ```
   The script will process any new CSV files in the configured S3 prefix and update the Snowflake table accordingly.
