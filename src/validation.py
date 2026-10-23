from dataclasses import dataclass
from typing import Optional
import pandas as pd
from datetime import datetime


@dataclass
class ValidationResult:
    """Result of record validation."""
    is_valid: bool
    record: dict
    error: Optional[str] = None


CHEMA_CONFIG = {
    "order_id": {"type": str, "nullable": False},
    "customer_id": {"type": str, "nullable": False},
    "order_date": {"type": str, "nullable": False},
    "amount": {"type": (int, float), "nullable": False},
    "status": {"type": str, "nullable": False},
}

VALID_STATUSES = {"pending", "completed", "cancelled", "shipped"}


def validate_schema(df: pd.DataFrame) -> None:
    """Validate that CSV has required columns."""
    required_columns = set(CHEMA_CONFIG.keys())
    actual_columns = set(df.columns)
    missing = required_columns - actual_columns
    extra = actual_columns - required_columns

    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if extra:
        raise ValueError(f"Unexpected columns in CSV: {extra}")


def validate_record(record: dict) -> ValidationResult:
    """Validate individual record against schema."""
    errors = []

    for column, config in CHEMA_CONFIG.items():
        value = record.get(column)

        # Check nullability
        if value is None or (isinstance(value, str) and value.strip() == ""):
            if not config["nullable"]:
                errors.append(f"Column '{column}' is required but null")
            continue

        # Type validation
        expected_type = config["type"]
        if isinstance(value, str) and value.strip() == "":
            if not config["nullable"]:
                errors.append(f"Column '{column}' cannot be empty")
            continue

        if not isinstance(value, expected_type):
            try:
                if "float" in str(expected_type) or "int" in str(expected_type):
                    float(value) if isinstance(expected_type, tuple) else int(value)
            except (ValueError, TypeError):
                errors.append(f"Column '{column}' has invalid type: {type(value).__name__}, expected {expected_type}")

    # Business rule validation
    if "status" in record and record["status"] not in VALID_STATUSES:
        errors.append(f"Column 'status' must be one of {VALID_STATUSES}, got {record['status']}")

    # Date format validation
    if "order_date" in record:
        try:
            datetime.fromisoformat(record["order_date"])
        except (ValueError, TypeError):
            errors.append(f"Column 'order_date' must be ISO format (YYYY-MM-DD), got {record['order_date']}")

    if errors:
        return ValidationResult(is_valid=False, record=record, error="; ".join(errors))
    return ValidationResult(is_valid=True, record=record)


def validate_dataframe(df: pd.DataFrame) -> tuple[list[dict], list[tuple[dict, str]]]:
    """
    Validate all records in DataFrame.
    Returns: (valid_records, rejected_records_with_errors)
    """
    validate_schema(df)
    valid_records = []
    rejected_records = []

    for _, row in df.iterrows():
        record = row.to_dict()
        result = validate_record(record)
        if result.is_valid:
            valid_records.append(record)
        else:
            rejected_records.append((record, result.error))

    return valid_records, rejected_records


def check_duplicates(records: list[dict]) -> tuple[list[dict], list[tuple[dict, str]]]:
    """
    Check for duplicate order_id within current batch.
    Duplicates are rejected to prevent data integrity issues.
    """
    seen = {}
    valid = []
    duplicates = []

    for record in records:
        order_id = record.get("order_id")
        if order_id in seen:
            duplicates.append((record, f"Duplicate order_id: {order_id}"))
        else:
            seen[order_id] = True
            valid.append(record)

    return valid, duplicates
