import os
import logging
import tempfile
import csv
from datetime import datetime
from .utils import (
    get_s3_client,
    list_new_files,
    validate_record,
    transform_record,
    upload_to_stage,
    copy_into_table,
    load_state,
    save_state
)
from .config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[logging.StreamHandler()]
)

def process_file(s3_client, key, last_modified):
    logger = logging.getLogger(__name__)
    logger.info(f"Processing file: {key}")
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.csv') as tmp_clean:
        cleaned_file_path = tmp_clean.name
    try:
        # Download file
        s3_client.download_file(Config.S3_BUCKET, key, '/tmp/original.csv')
        # Read and validate
        with open('/tmp/original.csv', 'r', newline='') as f_in, open(cleaned_file_path, 'w', newline='') as f_out:
            reader = csv.DictReader(f_in)
            writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                try:
                    validate_record(row)
                    transformed = transform_record(row)
                    writer.writerow(transformed)
                except Exception as e:
                    logger.warning(f"Skipping invalid record in {key}: {e}")
        # Upload to Snowflake stage
        stage_name = f"@{Config.SNOWFLAKE_SCHEMA}.stg_orders"
        upload_to_stage(cleaned_file_path, stage_name)
        # Copy into table
        copy_into_table(stage_name, os.path.basename(cleaned_file_path))
        logger.info(f"Successfully processed {key}")
    finally:
        os.remove(cleaned_file_path)
        if os.path.exists('/tmp/original.csv'):
            os.remove('/tmp/original.csv')

def main():
    logger = logging.getLogger(__name__)
    state = load_state()
    last_processed = state['last_processed']
    s3_client = get_s3_client()
    new_files = list_new_files(s3_client, last_processed)
    if not new_files:
        logger.info("No new files to process.")
        return
    for key in new_files:
        obj = s3_client.head_object(Bucket=Config.S3_BUCKET, Key=key)
        last_modified = obj['LastModified']
        process_file(s3_client, key, last_modified)
        save_state(last_modified)
    logger.info("ETL run completed.")

if __name__ == "__main__":
    main()
