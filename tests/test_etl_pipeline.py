import io
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from src.etl_pipeline import CustomerTotalsETL
from src.config import Config

class TestCustomerTotalsETL(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.config.S3_SOURCE_URI = "s3://test-bucket/input/sample-orders.csv"
        self.config.S3_TARGET_URI = "s3://test-bucket/output/customer_totals.csv"

    def test_parse_s3_uri(self):
        bucket, key = Config.parse_s3_uri("s3://mybucket/path/to/file.csv")
        self.assertEqual(bucket, "mybucket")
        self.assertEqual(key, "path/to/file.csv")

    def test_transform_valid_data(self):
        etl = CustomerTotalsETL.__new__(CustomerTotalsETL)
        etl.config = self.config
        raw_data = pd.DataFrame({
            "order_id": [1, 2, 3, 4],
            "customer_id": [101, 101, 102, 101],
            "amount": [50.0, 25.5, 100.0, 10.0]
        })
        
        result = etl.transform(raw_data)
        
        self.assertEqual(len(result), 2)
        row_101 = result[result["customer_id"] == 101].iloc[0]
        self.assertEqual(row_101["total_amount"], 85.5)
        self.assertEqual(row_101["order_count"], 3)
        
        row_102 = result[result["customer_id"] == 102].iloc[0]
        self.assertEqual(row_102["total_amount"], 100.0)
        self.assertEqual(row_102["order_count"], 1)

    def test_transform_handles_missing_and_invalid(self):
        etl = CustomerTotalsETL.__new__(CustomerTotalsETL)
        etl.config = self.config
        raw_data = pd.DataFrame({
            "order_id": [1, 2, 3],
            "customer_id": [101, None, 102],
            "amount": [50.0, 25.5, "invalid"]
        })
        
        result = etl.transform(raw_data)
        self.assertEqual(len(result), 1)
        row = result.iloc[0]
        self.assertEqual(row["customer_id"], 101)
        self.assertEqual(row["total_amount"], 50.0)
        self.assertEqual(row["order_count"], 1)

    @patch("boto3.client")
    def test_extract_calls_s3(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        csv_content = b"order_id,customer_id,amount\n1,101,50.0\n"
        mock_s3.get_object.return_value = {"Body": io.BytesIO(csv_content)}

        etl = CustomerTotalsETL(config=self.config)
        df = etl.extract()

        mock_s3.get_object.assert_called_once_with(Bucket="test-bucket", Key="input/sample-orders.csv")
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["customer_id"], 101)

if __name__ == "__main__":
    unittest.main()
