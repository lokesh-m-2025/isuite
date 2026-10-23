import pytest
from datetime import datetime
from src.validation import (
    validate_record,
    validate_dataframe,
    check_duplicates,
    ValidationResult
)


class TestValidateRecord:
    """Test individual record validation."""

    def test_valid_record(self):
        """Test validation of correct record."""
        record = {
            "order_id": "ORD-001",
            "customer_id": "CUST-001",
            "order_date": "2024-01-15",
            "amount": 99.99,
            "status": "completed"
        }
        result = validate_record(record)
        assert result.is_valid
        assert result.error is None

    def test_missing_required_field(self):
        """Test record with missing required field."""
        record = {
            "order_id": "ORD-001",
            "customer_id": "CUST-001",
            "order_date": "2024-01-15",
            # amount missing
            "status": "completed"
        }
        result = validate_record(record)
        assert not result.is_valid
        assert "amount" in result.error.lower()

    def test_null_required_field(self):
        """Test record with null required field."""
        record = {
            "order_id": "ORD-001",
            "customer_id": None,
            "order_date": "2024-01-15",
            "amount": 99.99,
            "status": "completed"
        }
        result = validate_record(record)
        assert not result.is_valid
        assert "customer_id" in result.error.lower()

    def test_empty_string_required_field(self):
        """Test record with empty string in required field."""
        record = {
            "order_id": "",
            "customer_id": "CUST-001",
            "order_date": "2024-01-15",
            "amount": 99.99,
            "status": "completed"
        }
        result = validate_record(record)
        assert not result.is_valid
        assert "order_id" in result.error.lower()

    def test_invalid_status(self):
        """Test record with invalid status value."""
        record = {
            "order_id": "ORD-001",
            "customer_id": "CUST-001",
            "order_date": "2024-01-15",
            "amount": 99.99,
            "status": "invalid_status"
        }
        result = validate_record(record)
        assert not result.is_valid
        assert "status" in result.error.lower()

    def test_invalid_date_format(self):
        """Test record with invalid date format."""
        record = {
            "order_id": "ORD-001",
            "customer_id": "CUST-001",
            "order_date": "15/01/2024",  # Wrong format
            "amount": 99.99,
            "status": "completed"
        }
        result = validate_record(record)
        assert not result.is_valid
        assert "order_date" in result.error.lower()

    def test_invalid_amount_type(self):
        """Test record with invalid amount type."""
        record = {
            "order_id": "ORD-001",
            "customer_id": "CUST-001",
            "order_date": "2024-01-15",
            "amount": "not_a_number",
            "status": "completed"
        }
        result = validate_record(record)
        assert not result.is_valid
        assert "amount" in result.error.lower()


class TestCheckDuplicates:
    """Test duplicate detection."""

    def test_no_duplicates(self):
        """Test records with no duplicates."""
        records = [
            {"order_id": "ORD-001", "customer_id": "CUST-001", "amount": 100},
            {"order_id": "ORD-002", "customer_id": "CUST-002", "amount": 200},
        ]
        valid, duplicates = check_duplicates(records)
        assert len(valid) == 2
        assert len(duplicates) == 0

    def test_duplicate_order_ids(self):
        """Test detection of duplicate order_ids."""
        records = [
            {"order_id": "ORD-001", "customer_id": "CUST-001", "amount": 100},
            {"order_id": "ORD-001", "customer_id": "CUST-002", "amount": 200},
        ]
        valid, duplicates = check_duplicates(records)
        assert len(valid) == 1
        assert len(duplicates) == 1
        assert "duplicate" in duplicates[0][1].lower()


class TestValidateDataFrame:
    """Test full DataFrame validation."""

    def test_valid_dataframe(self):
        """Test validation of valid DataFrame."""
        import pandas as pd
        df = pd.DataFrame([
            {
                "order_id": "ORD-001",
                "customer_id": "CUST-001",
                "order_date": "2024-01-15",
                "amount": 99.99,
                "status": "completed"
            },
            {
                "order_id": "ORD-002",
                "customer_id": "CUST-002",
                "order_date": "2024-01-16",
                "amount": 150.00,
                "status": "pending"
            },
        ])
        valid, rejected = validate_dataframe(df)
        assert len(valid) == 2
        assert len(rejected) == 0

    def test_mixed_valid_invalid(self):
        """Test DataFrame with mix of valid and invalid records."""
        import pandas as pd
        df = pd.DataFrame([
            {
                "order_id": "ORD-001",
                "customer_id": "CUST-001",
                "order_date": "2024-01-15",
                "amount": 99.99,
                "status": "completed"
            },
            {
                "order_id": None,  # Invalid: missing order_id
                "customer_id": "CUST-002",
                "order_date": "2024-01-16",
                "amount": 150.00,
                "status": "pending"
            },
        ])
        valid, rejected = validate_dataframe(df)
        assert len(valid) == 1
        assert len(rejected) == 1
