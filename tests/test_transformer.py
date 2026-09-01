import pytest
import pandas as pd
from src.transformer import OrderTransformer

def test_transform_valid_records():
    data = {
        "order_id": [1, 2, 3, 4],
        "customer_id": ["C101", "C102", "C101", "C103"],
        "amount": [100.50, 200.00, 50.25, 75.00]
    }
    df = pd.DataFrame(data)
    transformer = OrderTransformer()
    res, metrics = transformer.transform(df)
    
    assert len(res) == 3
    c101_row = res[res["customer_id"] == "C101"].iloc[0]
    assert c101_row["total_amount"] == 150.75
    assert c101_row["order_count"] == 2
    assert metrics["raw_records"] == 4
    assert metrics["valid_records"] == 4

def test_transform_handles_missing_and_malformed_data():
    data = {
        "order_id": [1, 2, 3, 4, 5],
        "customer_id": ["C101", None, "C102", "C101", "C103"],
        "amount": [100.00, 50.00, "invalid_number", 200.00, 10.00]
    }
    df = pd.DataFrame(data)
    transformer = OrderTransformer()
    res, metrics = transformer.transform(df)
    
    assert metrics["dropped_missing_customer"] == 1
    assert metrics["dropped_invalid_amount"] == 1
    assert metrics["valid_records"] == 3
    assert len(res) == 2

def test_validate_schema_missing_column():
    df = pd.DataFrame({"order_id": [1], "customer_id": ["C101"]})
    transformer = OrderTransformer()
    with pytest.raises(ValueError, match="Source CSV missing required columns"):
        transformer.validate_schema(df)
