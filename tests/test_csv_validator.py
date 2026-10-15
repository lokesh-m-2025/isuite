import unittest
import io
import pandas as pd
from src.csv_validator import CSVValidator


class TestCSVValidator(unittest.TestCase):
    def setUp(self):
        self.validator = CSVValidator(
            ["order_id", "customer_id", "order_date", "amount", "status"]
        )

    def test_valid_csv(self):
        """Test parsing a valid CSV."""
        csv_data = (
            "order_id,customer_id,order_date,amount,status\n"
            "ORD001,CUST001,2024-01-15,150.50,completed\n"
            "ORD002,CUST002,2024-01-15,200.00,pending\n"
        )
        csv_bytes = io.BytesIO(csv_data.encode("utf-8"))

        valid_df, malformed = self.validator.validate_and_parse(csv_bytes)

        self.assertEqual(len(valid_df), 2)
        self.assertEqual(len(malformed), 0)
        self.assertListEqual(
            list(valid_df.columns),
            ["order_id", "customer_id", "order_date", "amount", "status"],
        )

    def test_csv_with_null_values(self):
        """Test CSV with null/empty values."""
        csv_data = (
            "order_id,customer_id,order_date,amount,status\n"
            "ORD001,CUST001,2024-01-15,150.50,completed\n"
            "ORD002,,2024-01-15,200.00,pending\n"
        )
        csv_bytes = io.BytesIO(csv_data.encode("utf-8"))

        valid_df, malformed = self.validator.validate_and_parse(csv_bytes)

        self.assertEqual(len(valid_df), 1)
        self.assertEqual(len(malformed), 1)
        self.assertIn("null values", malformed[0]["error_reason"].lower())

    def test_csv_missing_required_column(self):
        """Test CSV with missing required column."""
        csv_data = (
            "order_id,customer_id,amount,status\n"
            "ORD001,CUST001,150.50,completed\n"
        )
        csv_bytes = io.BytesIO(csv_data.encode("utf-8"))

        with self.assertRaises(ValueError) as context:
            self.validator.validate_and_parse(csv_bytes)

        self.assertIn("order_date", str(context.exception))

    def test_csv_with_extra_columns(self):
        """Test CSV with extra columns (should be ignored)."""
        csv_data = (
            "order_id,customer_id,order_date,amount,status,extra_column\n"
            "ORD001,CUST001,2024-01-15,150.50,completed,extra_value\n"
        )
        csv_bytes = io.BytesIO(csv_data.encode("utf-8"))

        valid_df, malformed = self.validator.validate_and_parse(csv_bytes)

        self.assertEqual(len(valid_df), 1)
        self.assertEqual(len(malformed), 0)
        self.assertNotIn("extra_column", valid_df.columns)

    def test_csv_with_empty_strings(self):
        """Test CSV with empty string values."""
        csv_data = (
            "order_id,customer_id,order_date,amount,status\n"
            "ORD001,CUST001,2024-01-15,150.50,completed\n"
            "ORD002,CUST002,,200.00,pending\n"
        )
        csv_bytes = io.BytesIO(csv_data.encode("utf-8"))

        valid_df, malformed = self.validator.validate_and_parse(csv_bytes)

        self.assertEqual(len(valid_df), 1)
        self.assertEqual(len(malformed), 1)
        self.assertIn("empty", malformed[0]["error_reason"].lower())


if __name__ == "__main__":
    unittest.main()
