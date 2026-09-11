import unittest
import pandas as pd
from transformer import OrderTransformer


class TestOrderTransformer(unittest.TestCase):
    """Tests for OrderTransformer."""

    def setUp(self):
        self.transformer = OrderTransformer()

    def test_single_customer_single_order(self):
        """Single customer with one order."""
        df = pd.DataFrame({
            "customer_id": ["C001"],
            "amount": [100.0],
        })
        result = self.transformer.aggregate_by_customer(df)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["customer_id"], "C001")
        self.assertEqual(result.iloc[0]["total_amount"], 100.0)
        self.assertEqual(result.iloc[0]["order_count"], 1)

    def test_single_customer_multiple_orders(self):
        """Single customer with multiple orders."""
        df = pd.DataFrame({
            "customer_id": ["C001", "C001", "C001"],
            "amount": [100.0, 50.0, 75.5],
        })
        result = self.transformer.aggregate_by_customer(df)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["customer_id"], "C001")
        self.assertEqual(result.iloc[0]["total_amount"], 225.5)
        self.assertEqual(result.iloc[0]["order_count"], 3)

    def test_multiple_customers(self):
        """Multiple customers with multiple orders."""
        df = pd.DataFrame({
            "customer_id": ["C001", "C002", "C001", "C003"],
            "amount": [100.0, 200.0, 50.0, 300.0],
        })
        result = self.transformer.aggregate_by_customer(df)
        self.assertEqual(len(result), 3)
        
        # Check sorting
        self.assertEqual(result.iloc[0]["customer_id"], "C001")
        self.assertEqual(result.iloc[1]["customer_id"], "C002")
        self.assertEqual(result.iloc[2]["customer_id"], "C003")
        
        # Check aggregation
        c001 = result[result["customer_id"] == "C001"].iloc[0]
        self.assertEqual(c001["total_amount"], 150.0)
        self.assertEqual(c001["order_count"], 2)

    def test_currency_rounding(self):
        """Total amount should be rounded to 2 decimal places."""
        df = pd.DataFrame({
            "customer_id": ["C001", "C001"],
            "amount": [10.111, 20.222],
        })
        result = self.transformer.aggregate_by_customer(df)
        # 10.111 + 20.222 = 30.333, rounded to 30.33
        self.assertEqual(result.iloc[0]["total_amount"], 30.33)

    def test_empty_dataframe(self):
        """Empty DataFrame should return empty result with correct columns."""
        df = pd.DataFrame()
        result = self.transformer.aggregate_by_customer(df)
        self.assertEqual(len(result), 0)
        self.assertListEqual(
            list(result.columns), ["customer_id", "total_amount", "order_count"]
        )

    def test_output_column_types(self):
        """Output columns should have correct types."""
        df = pd.DataFrame({
            "customer_id": ["C001"],
            "amount": [100.0],
        })
        result = self.transformer.aggregate_by_customer(df)
        self.assertEqual(result["customer_id"].dtype, object)
        self.assertTrue(result["total_amount"].dtype in [float, "float64"])
        self.assertEqual(result["order_count"].dtype, "int64")


if __name__ == "__main__":
    unittest.main()
