"""Tests for schema validation."""

import pytest
from src.schema import SchemaValidator, OrderSchema


class TestSchemaValidator:
    """Tests for SchemaValidator class."""

    def test_validate_columns_success(self):
        """Test successful column validation."""
        record = {
            "order_id": "123",
            "customer_id": "cust_456",
            "amount": "99.99",
            "order_date": "2024-01-15",
        }
        is_valid, error = SchemaValidator.validate_columns(record)
        assert is_valid is True
        assert error is None

    def test_validate_columns_missing(self):
        """Test validation with missing columns."""
        record = {
            "order_id": "123",
            "customer_id": "cust_456",
            # Missing amount and order_date
        }
        is_valid, error = SchemaValidator.validate_columns(record)
        assert is_valid is False
        assert "Missing required columns" in error
        assert "amount" in error
        assert "order_date" in error

    def test_validate_record_empty_order_id(self):
        """Test that empty order_id is rejected."""
        record = {
            "order_id": "",
            "customer_id": "cust_456",
            "amount": "99.99",
            "order_date": "2024-01-15",
        }
        is_valid, error = SchemaValidator.validate_record(record)
        assert is_valid is False
        assert "order_id" in error

    def test_validate_record_empty_customer_id(self):
        """Test that empty customer_id is rejected."""
        record = {
            "order_id": "123",
            "customer_id": "",
            "amount": "99.99",
            "order_date": "2024-01-15",
        }
        is_valid, error = SchemaValidator.validate_record(record)
        assert is_valid is False
        assert "customer_id" in error

    def test_validate_record_invalid_amount(self):
        """Test that non-numeric amount is rejected."""
        record = {
            "order_id": "123",
            "customer_id": "cust_456",
            "amount": "not_a_number",
            "order_date": "2024-01-15",
        }
        is_valid, error = SchemaValidator.validate_record(record)
        assert is_valid is False
        assert "amount" in error

    def test_validate_record_negative_amount(self):
        """Test that negative amount is rejected."""
        record = {
            "order_id": "123",
            "customer_id": "cust_456",
            "amount": "-50.00",
            "order_date": "2024-01-15",
        }
        is_valid, error = SchemaValidator.validate_record(record)
        assert is_valid is False
        assert "non-negative" in error

    def test_validate_record_success(self):
        """Test successful record validation."""
        record = {
            "order_id": "123",
            "customer_id": "cust_456",
            "amount": "99.99",
            "order_date": "2024-01-15",
        }
        is_valid, error = SchemaValidator.validate_record(record)
        assert is_valid is True
        assert error is None

    def test_coerce_types_success(self):
        """Test successful type coercion."""
        record = {
            "order_id": "123",
            "customer_id": "cust_456",
            "amount": "99.99",
            "order_date": "2024-01-15",
        }
        schema, error = SchemaValidator.coerce_types(record)
        assert error is None
        assert schema is not None
        assert schema.order_id == "123"
        assert schema.customer_id == "cust_456"
        assert schema.amount == 99.99
        assert schema.order_date == "2024-01-15"

    def test_coerce_types_integer_amount(self):
        """Test coercion with integer amount."""
        record = {
            "order_id": "123",
            "customer_id": "cust_456",
            "amount": "100",
            "order_date": "2024-01-15",
        }
        schema, error = SchemaValidator.coerce_types(record)
        assert error is None
        assert schema.amount == 100.0

    def test_coerce_types_with_whitespace(self):
        """Test coercion strips whitespace from strings."""
        record = {
            "order_id": "  123  ",
            "customer_id": "  cust_456  ",
            "amount": "99.99",
            "order_date": "  2024-01-15  ",
        }
        schema, error = SchemaValidator.coerce_types(record)
        assert error is None
        assert schema.order_id == "123"
        assert schema.customer_id == "cust_456"
        assert schema.order_date == "2024-01-15"
