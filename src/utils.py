import os
import json
import logging
import boto3
import csv
from datetime import datetime
from snowflake.connector import connect
from .config import Config

logger = logging.getLogger(__name__)

def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
        region_name=Config.AWS_REGION
    )

def get_snowflake_connection():
    return connect(
        user=Config.SNOWFLAKE_USER,
        password=Config.SNOWFLAKE_PASSWORD,
        account=Config.SNOWFLAKE_ACCOUNT,
        warehouse=Config.SNOWFLAKE_WAREHOUSE,
        database=Config.SNOWFLAKE_DATABASE,
        schema=Config.SNOWFLAKE_SCHEMA
    )

def list_new_files(s3_client, last_processed_timestamp):
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=Config.S3_BUCKET, Prefix=Config.S3_PREFIX)
    new_files = []
    for page in page_iterator:
        for obj in page.get('Contents', []):
            key = obj['Key']
            if not key.endswith('.csv'):
                continue
            last_modified = obj['LastModified']
            if last_modified > last_processed_timestamp:
                new_files.append((key, last_modified))
    new_files.sort(key=lambda x: x[1])
    return [k for k, _ in new_files]

def validate_record(record):
    required_fields = ['order_id', 'customer_id', 'order_date', 'amount']
    for field in required_fields:
        if field not in record or record[field] == '':
            raise ValueError(f"Missing required field: {field}")
    try:
        int(record['order_id'])
        int(record['customer_id'])
        datetime.strptime(record['order_date'], '%Y-%m-%d')
        float(record['amount'])
    except Exception as e:
        raise ValueError(f"Type conversion error: {e}")

def transform_record(record):
    record['order_id'] = int(record['order_id'])
    record['customer_id'] = int(record['customer_id'])
    record['order_date'] = record['order_date']
    record['amount'] = float(record['amount'])
    return record

def upload_to_stage(local_file_path, stage_name):
    conn = get_snowflake_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"PUT file://{local_file_path} {stage_name} AUTO_COMPRESS=TRUE")
    finally:
        conn.close()

def copy_into_table(stage_name, file_name):
    conn = get_snowflake_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                COPY INTO {Config.SNOWFLAKE_TABLE}
                FROM {stage_name}/{file_name}
                FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ',' SKIP_HEADER = 1)
                ON_ERROR = 'SKIP_FILE'
            """)
    finally:
        conn.close()

def load_state():
    if not os.path.exists(Config.STATE_FILE):
        return {'last_processed': datetime.min}
    with open(Config.STATE_FILE, 'r') as f:
        data = json.load(f)
    return {'last_processed': datetime.fromisoformat(data['last_processed'])}

def save_state(last_processed):
    with open(Config.STATE_FILE, 'w') as f:
        json.dump({'last_processed': last_processed.isoformat()}, f)
