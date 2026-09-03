# S3 Order Processing ETL Pipeline

Production-grade Python ETL pipeline that reads order records from `s3://your-bucket/input/orders.csv`, aggregates order amounts and counts per customer, and writes the output to `s3://your-bucket/output/customer_totals.csv` without modifying the source file.

## How to run this

### 1. Prerequisites
- Python 3.9+
- AWS Account with read access to the input S3 object and write access to the output S3 location (or local credentials / IAM role configured).

### 2. Installing dependencies
Install the required Python packages:
```bash preference-shell
pip install boto3 pandas pydantic python-dotenv pytest moto
```

### 3. Configuring credentials
Copy `.env.example` to `.env`:
```bash preference-shell
cp .env.example .env
```
Fill in real configuration values in `.env` only. `.env.example` stays blank so it can be safely committed to source control. `.gitignore` already excludes `.env` from version control, so no further action is needed to protect your secrets.

### 4. Running it
Execute the ETL pipeline:
```bash preference-shell
python main.py
```
Run unit tests:
```bash preference-shell
pytest
```
