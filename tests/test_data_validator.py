import pandas as pd
import pytest
from src.data_validator import DataValidator


@pytest.fixture
def validator():
    return DataValidator()


def test_no_duplicates(validator):
    """Test validation passes for data without duplicates."""
    df = pd.DataFrame({
        "order_id": [1, 2, 3],
        "customer_id": [10, 20, 30],
        "amount": [100.50, 200.75, 150.00],
    })
    valid_df, invalid_df = validator.validate(df)
    assert len(valid_df) == 3
    assert invalid_df.empty


def test_duplicate_rows_detected(validator):
    """Test validation detects complete duplicate rows."""
    df = pd.DataFrame({
        "order_id": [1, 2, 1, 3],
        "customer_id": [10, 20, 10, 30],
        "amount": [100.50, 200.75, 100.50, 150.00],
    })
    valid_df, invalid_df = validator.validate(df)
    assert len(valid_df) == 3
    assert len(invalid_df) == 1


def test_empty_dataframe(validator):
    """Test validation handles empty DataFrame gracefully."""
    df = pd.DataFrame()
    valid_df, invalid_df = validator.validate(df)
    assert valid_df.empty
    assert invalid_df.empty
