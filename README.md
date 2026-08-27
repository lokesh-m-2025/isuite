# S3 Customer Orders Aggregate ETL Pipeline

Production-ready Python ETL job to aggregate order amounts and count per customer from S3.

## How to run this

1. Prerequisites
   - Python 3.9+ environment.
   - Access permissions to target AWS S3 bucket `ignitho-development-bucket`.

2. Installing dependencies
   Run the command:
   ```bash
   pip install boto3 pandas python-dotenv
   ```

3. Configuring credentials
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Fill in real AWS credentials and S3 configuration settings in `.env` only. `.env.example` stays blank so it can be committed. `.gitignore` already excludes `.env` from version control, so nothing further needs doing there.

4. Running it
   Execute the ETL job:
   ```bash
   python main.py
   ```
