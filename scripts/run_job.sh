#!/usr/bin/env bash
set -euo pipefail

INPUT_PATH="${S3_INPUT_PATH:-s3://your-bucket/input/orders.csv}"
OUTPUT_PATH="${S3_OUTPUT_PATH:-s3://your-bucket/output/customer_totals.csv}"

echo "Starting PySpark ETL Job..."

spark-submit \
  --master yarn \
  --deploy-mode cluster \
  --packages org.apache.hadoop:hadoop-aws:3.3.4 \
  src/etl_job.py \
  --input-path "$INPUT_PATH" \
  --output-path "$OUTPUT_PATH"

echo "Job completed."
