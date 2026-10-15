import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from src.schema_validator import SchemaValidator


@pytest.fixture
def sample_schema():
    """Create a temporary schema file for testing."""
    schema = {
        "columns": [
            {"name": "order_id", "type": "integer", "nullable": False},
            {"name": "customer_id", "type": "integer", "nullable": False},
            {"name": "amount", "type": "float", "nullable": False},
            {"name": "status", "type": "string", "nullable": False},
            {"name": "notes", "type": "string", "nullable": True},
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(schema, f)
        schema_path = f.name
    yield schema_path
    Path(schema_path).unlink()


def test_valid_dataframe(sample_schema):
    """Test validation passes for valid data."""
    validator = SchemaValidator(sample_schema)
    df = pd.DataFrame({
        "order_id": [1, 2, 3],
        "customer_id": [10, 20, 30],
        "amount": [100.50, 200.75, 150.00],
        "status": ["COMPLETED", "PENDING", "CANCELLED"],
        "notes": [None, "urgent", None],
    })
    valid_df, invalid_df = validator.validate(df)
    assert len(valid_df) == 3
    assert invalid_df.empty


def test_missing_required_column(sample_schema):
    """Test validation fails when required column is missing."""
    validator = SchemaValidator(sample_schema)
    df = pd.DataFrame({
        "order_id": [1, 2],
        "customer_id": [10, 20],
        "amount": [100.50, 200.75],
        "notes": [None, "urgent"],
    })
    valid_df, invalid_df = validator.validate(df)
    assert valid_df.empty
    assert len(invalid_df) == 2


def test_null_in_required_column(sample_schema):
    """Test validation fails when required column contains null."""
    validator = SchemaValidator(sample_schema)
    df = pd.DataFrame({
        "order_id": [1, None, 3],
        "customer_id": [10, 20, 30],
        "amount": [100.50, 200.75, 150.00],
        "status": ["COMPLETED", "PENDING", "CANCELLED"],
        "notes": [None, None, None],
    })
    valid_df, invalid_df = validator.validate(df)
    assert len(valid_df) == 2
    assert len(invalid_df) == 1


def test_null_in_nullable_column(sample_schema):
    """Test validation passes when nullable column contains null."""
    validator = SchemaValidator(sample_schema)
    df = pd.DataFrame({
        "order_id": [1, 2],
        "customer_id": [10, 20],
        "amount": [100.50, 200.75],
        "status": ["COMPLETED", "PENDING"],
        "notes": [None, None],
    })
    valid_df, invalid_df = validator.validate(df)
    assert len(valid_df) == 2
    assert invalid_df.empty


def test_type_validation_integer(sample_schema):
    """Test type validation for integer columns."""
    validator = SchemaValidator(sample_schema)
    df = pd.DataFrame({
        "order_id": [1, "invalid", 3],
        "customer_id": [10, 20, 30],
        "amount": [100.50, 200.75, 150.00],
        "status": ["COMPLETED", "PENDING", "CANCELLED"],
        "notes": [None, None, None],
    })
    valid_df, invalid_df = validator.validate(df)
    assert len(valid_df) <= 2
    assert len(invalid_df) >= 1


def test_extra_columns_ignored(sample_schema):
    """Test that extra columns are ignored without error."""
    validator = SchemaValidator(sample_schema)
    df = pd.DataFrame({
        "order_id": [1, 2],
        "customer_id": [10, 20],
        "amount": [100.50, 200.75],
        "status": ["COMPLETED", "PENDING"],
        "notes": [None, None],
        "extra_column": ["x", "y"],
    })
    valid_df, invalid_df = validator.validate(df)
    assert len(valid_df) == 2
    assert "extra_column" not in valid_df.columns
    assert invalid_df.empty
