"""Unit tests for ETL transformation logic."""

import unittest
from io import StringIO
from unittest.mock import Mock, patch

import pandas as pd

from src.etl import OrderAggregationETL


class TestOrderAggregationETL(unittest.TestCase):
    """Test cases for OrderAggregationETL."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_s3_client = Mock()
        self.mock_logger = Mock()
        self.etl = OrderAggregationETL(
            s3_client=self.mock_s3_client,
            logger=self.mock_logger,
        )

    def test_validate_schema_missing_column(self):
        """Test schema validation detects missing required columns."""
        df = pd.DataFrame({"order_id": [1], "customer_id": [100]})
        with self.assertRaises(ValueError) as context:
            self.etl._validate_schema(df)
        self.assertIn("amount", str(context.exception))

    def test_validate_data_types_valid_rows(self):
        """Test data type validation accepts valid rows."""
        df = pd.DataFrame({
            "order_id": ["O1", "O2"],
            "customer_id": ["C1", "C2"],
            "amount": ["100.50", "200.00"],
        })
        valid_df, rejected_df = self.etl._validate_data_types(df)
        self.assertEqual(len(valid_df), 2)
        self.assertEqual(len(rejected_df), 0)
        self.assertEqual(valid_df["amount"].dtype, float)

    def test_validate_data_types_null_customer_id(self):
        """Test data type validation rejects null customer_id."""
        df = pd.DataFrame({
            "order_id": ["O1", "O2"],
            "customer_id": ["C1", None],
            "amount": [100.50, 200.00],
        })
        valid_df, rejected_df = self.etl._validate_data_types(df)
        self.assertEqual(len(valid_df), 1)
        self.assertEqual(len(rejected_df), 1)
        self.assertIn("null", rejected_df.iloc[0]["rejection_reason"])

    def test_validate_data_types_invalid_amount(self):
        """Test data type validation rejects non-numeric amount."""
        df = pd.DataFrame({
            "order_id": ["O1", "O2"],
            "customer_id": ["C1", "C2"],
            "amount": ["100.50", "invalid"],
        })
        valid_df, rejected_df = self.etl._validate_data_types(df)
        self.assertEqual(len(valid_df), 1)
        self.assertEqual(len(rejected_df), 1)
        self.assertIn("not numeric", rejected_df.iloc[0]["rejection_reason"])

    def test_aggregate_basic(self):
        """Test aggregation groups correctly by customer_id."""
        df = pd.DataFrame({
            "order_id": ["O1", "O2", "O3"],
            "customer_id": ["C1", "C1", "C2"],
            "amount": [100.0, 50.0, 200.0],
        })
        aggregated = self.etl._aggregate(df)
        self.assertEqual(len(aggregated), 2)
        c1 = aggregated[aggregated["customer_id"] == "C1"].iloc[0]
        self.assertEqual(c1["total_amount"], 150.0)
        self.assertEqual(c1["order_count"], 2)

    def test_aggregate_rounding(self):
        """Test aggregation rounds amounts to 2 decimal places."""
        df = pd.DataFrame({
            "order_id": ["O1", "O2"],
            "customer_id": ["C1", "C1"],
            "amount": [100.123, 50.456],
        })
        aggregated = self.etl._aggregate(df)
        total = aggregated.iloc[0]["total_amount"]
        self.assertEqual(total, 150.58)

    def test_quality_checks_pass(self):
        """Test quality checks pass for valid data."""
        source_df = pd.DataFrame({
            "order_id": ["O1", "O2", "O3"],
            "customer_id": ["C1", "C1", "C2"],
            "amount": [100.0, 50.0, 200.0],
        })
        aggregated_df = pd.DataFrame({
            "customer_id": ["C1", "C2"],
            "total_amount": [150.0, 200.0],
            "order_count": [2, 1],
        })
        result = self.etl._quality_checks(source_df, aggregated_df)
        self.assertTrue(result)

    def test_quality_checks_fail_customer_mismatch(self):
        """Test quality checks fail if customer count mismatches."""
        source_df = pd.DataFrame({
            "order_id": ["O1", "O2"],
            "customer_id": ["C1", "C2"],
            "amount": [100.0, 200.0],
        })
        aggregated_df = pd.DataFrame({
            "customer_id": ["C1"],
            "total_amount": [100.0],
            "order_count": [1],
        })
        result = self.etl._quality_checks(source_df, aggregated_df)
        self.assertFalse(result)

    def test_quality_checks_fail_amount_mismatch(self):
        """Test quality checks fail if total amount mismatches."""
        source_df = pd.DataFrame({
            "order_id": ["O1"],
            "customer_id": ["C1"],
            "amount": [100.0],
        })
        aggregated_df = pd.DataFrame({
            "customer_id": ["C1"],
            "total_amount": [99.0],
            "order_count": [1],
        })
        result = self.etl._quality_checks(source_df, aggregated_df)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
