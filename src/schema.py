"""Schema definition and validation for order data."""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class OrderSchema:
    """Schema for order records from input CSV."""

    order_id: str
    customer_id: str
    amount: float
    order_date: str


@dataclass
class CustomerTotalSchema:
    """Schema for customer aggregate output."""

    customer_id: str
    total_amount: float
    order_count: int


class SchemaValidator:
    """Validates records against the expected schema."""

    # Required columns in input CSV
    REQUIRED_COLUMNS = ["order_id", "customer_id", "amount", "order_date"]

    # Expected data types (flexible string-based validation since CSV is text)
    EXPECTED_TYPES = {
        "order_id": str,
        "customer_id": str,
        "amount": (int, float),
        "order_date": str,
    }

    @staticmethod
    def validate_columns(record: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate that all required columns are present.

        Args:
            record: Record dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        missing_columns = [
            col for col in SchemaValidator.REQUIRED_COLUMNS if col not in record
        ]

        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"

        return True, None

    @staticmethod
    def validate_record(record: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate a complete order record.

        Args:
            record: Record dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check columns
        is_valid, error = SchemaValidator.validate_columns(record)
        if not is_valid:
            return False, error

        # Validate order_id is not empty
        order_id = str(record.get("order_id", "")).strip()
        if not order_id:
            return False, "order_id cannot be empty"

        # Validate customer_id is not empty
        customer_id = str(record.get("customer_id", "")).strip()
        if not customer_id:
            return False, "customer_id cannot be empty"

        # Validate amount is numeric and positive
        amount_str = str(record.get("amount", "")).strip()
        try:
            amount = float(amount_str)
            if amount < 0:
                return False, f"amount must be non-negative, got {amount}"
        except (ValueError, TypeError):
            return False, f"amount must be numeric, got '{amount_str}'"

        # Validate order_date is not empty (format validation is optional)
        order_date = str(record.get("order_date", "")).strip()
        if not order_date:
            return False, "order_date cannot be empty"

        return True, None

    @staticmethod
    def coerce_types(record: Dict[str, Any]) -> tuple[OrderSchema, Optional[str]]:
        """Attempt to coerce record to proper types.

        Args:
            record: Record dictionary with string values

        Returns:
            Tuple of (OrderSchema or None, error_message)
        """
        try:
            return (
                OrderSchema(
                    order_id=str(record["order_id"]).strip(),
                    customer_id=str(record["customer_id"]).strip(),
                    amount=float(record["amount"]),
                    order_date=str(record["order_date"]).strip(),
                ),
                None,
            )
        except (ValueError, KeyError, TypeError) as e:
            return None, f"Type coercion failed: {str(e)}"
