import unittest
import pandas as pd
from validator import SchemaValidator, DataValidator


class TestSchemaValidator(unittest.TestCase):
    """Tests for SchemaValidator."""

    def setUp(self):
        self.validator = SchemaValidator(["customer_id", "amount"])

    def test_valid_schema(self):
        """Valid schema should return no errors."""
        df = pd.DataFrame(
            {"customer_id": ["C001"], "amount": [100.0]}
        )
        errors = self.validator.validate(df)
        self.assertEqual(errors, [])

    def test_missing_column(self):
        """Missing required column should return error."""
        df = pd.DataFrame({"customer_id": ["C001"]})
        errors = self.validator.validate(df)
        self.assertEqual(len(errors), 1)
        self.assertIn("amount", errors[0])

    def test_extra_columns_allowed(self):
        """Extra columns should not cause errors."""
        df = pd.DataFrame(
            {"customer_id": ["C001"], "amount": [100.0], "extra": ["data"]}
        )
        errors = self.validator.validate(df)
        self.assertEqual(errors, [])


class TestDataValidator(unittest.TestCase):
    """Tests for DataValidator."""

    def setUp(self):
        self.validator = DataValidator()

    def test_valid_records(self):
        """Valid records should pass validation."""
        df = pd.DataFrame({
            "customer_id": ["C001", "C002"],
            "amount": [100.0, 200.5],
        })
        valid, invalid = self.validator.validate_and_separate(df)
        self.assertEqual(len(valid), 2)
        self.assertEqual(len(invalid), 0)

    def test_null_customer_id(self):
        """Records with null customer_id should be rejected."""
        df = pd.DataFrame({
            "customer_id": ["C001", None, "C003"],
            "amount": [100.0, 200.0, 300.0],
        })
        valid, invalid = self.validator.validate_and_separate(df)
        self.assertEqual(len(valid), 2)
        self.assertEqual(len(invalid), 1)
        self.assertIn("customer_id", invalid.iloc[0]["_validation_error"])

    def test_null_amount(self):
        """Records with null amount should be rejected."""
        df = pd.DataFrame({
            "customer_id": ["C001", "C002"],
            "amount": [100.0, None],
        })
        valid, invalid = self.validator.validate_and_separate(df)
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(invalid), 1)

    def test_non_numeric_amount(self):
        """Records with non-numeric amount should be rejected."""
        df = pd.DataFrame({
            "customer_id": ["C001", "C002"],
            "amount": ["100.0", "invalid"],
        })
        valid, invalid = self.validator.validate_and_separate(df)
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(invalid), 1)

    def test_empty_dataframe(self):
        """Empty DataFrame should return empty results."""
        df = pd.DataFrame()
        valid, invalid = self.validator.validate_and_separate(df)
        self.assertEqual(len(valid), 0)
        self.assertEqual(len(invalid), 0)


if __name__ == "__main__":
    unittest.main()
