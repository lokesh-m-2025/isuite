# S3 Customer Orders Aggregation ETL Pipeline

Production-ready AWS Python ETL pipeline that extracts customer order data from S3, validates records, computes aggregations (`total_amount` and `order_count` per `customer_id`), and writes the processed output back to S3.

## How to run this

1. Prerequisites
Python 3.10+ installed on your machine. AWS credentials configured with appropriate read/write access permissions for `s3://ignitho-development-bucket`.

2. Installing dependencies
Run the following command to install the required Python packages:
```bash
pip install pandas>=2.0.0 boto3>=1.28.0 python-dotenv>=1.0.0 pydantic>=2.0.0 pytest>=7.4.0 moto>=4.2.0
```

3. Configuring credentials
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in real values in `.env` only. `.env.example` stays blank so it can be committed. `.gitignore` already excludes `.env` from version control, so nothing further needs doing there.

4. Running it
Execute the main ETL pipeline:
```bash
python -m src.pipeline
```

To execute the automated unit and integration tests:
```bash
pytest
```
