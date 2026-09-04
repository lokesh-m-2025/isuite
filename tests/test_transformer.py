"""Tests for data transformation logic."""

import pytest
from src.schema import OrderSchema, CustomerTotalSchema
from src.transformer import OrderTransformer


class TestOrderTransformer:
    """Tests for OrderTransformer class."""

    def test_aggregate_single_customer(self):
        """Test aggregation with single customer and multiple orders."""
        orders = [
            OrderSchema(
                order_id="1", customer_id="cust_1", amount=50.0, order_date="2024-01-01"
            ),
            OrderSchema(
                order_id="2", customer_id="cust_1", amount=30.0, order_date="2024-01-02"
            ),
            OrderSchema(
                order_id="3", customer_id="cust_1", amount=20.0, order_date="2024-01-03"
            ),
        ]

        results, metrics = OrderTransformer.aggregate_by_customer(orders)

        assert len(results) == 1
        assert results[0].customer_id == "cust_1"
        assert results[0].total_amount == 100.0
        assert results[0].order_count == 3
        assert metrics["unique_customers"] == 1
        assert metrics["total_orders_aggregated"] == 3
        assert metrics["total_amount"] == 100.0

    def test_aggregate_multiple_customers(self):
        """Test aggregation with multiple customers."""
        orders = [
            OrderSchema(
                order_id="1", customer_id="cust_1", amount=50.0, order_date="2024-01-01"
            ),
            OrderSchema(
                order_id="2", customer_id="cust_2", amount=75.0, order_date="2024-01-02"
            ),
            OrderSchema(
                order_id="3", customer_id="cust_1", amount=25.0, order_date="2024-01-03"
            ),
            OrderSchema(
                order_id="4", customer_id="cust_2", amount=100.0, order_date="2024-01-04"
            ),
        ]

        results, metrics = OrderTransformer.aggregate_by_customer(orders)

        assert len(results) == 2
        assert metrics["unique_customers"] == 2
        assert metrics["total_orders_aggregated"] == 4
        assert metrics["total_amount"] == 250.0

        # Check results are sorted by customer_id
        assert results[0].customer_id == "cust_1"
        assert results[0].total_amount == 75.0
        assert results[0].order_count == 2

        assert results[1].customer_id == "cust_2"
        assert results[1].total_amount == 175.0
        assert results[1].order_count == 2

    def test_aggregate_empty_list(self):
        """Test aggregation with empty order list."""
        orders = []
        results, metrics = OrderTransformer.aggregate_by_customer(orders)

        assert len(results) == 0
        assert metrics["unique_customers"] == 0
        assert metrics["total_orders_aggregated"] == 0
        assert metrics["total_amount"] == 0.0

    def test_to_csv_row(self):
        """Test conversion of customer total to CSV row."""
        customer_total = CustomerTotalSchema(
            customer_id="cust_1", total_amount=99.99, order_count=5
        )
        row = OrderTransformer.to_csv_row(customer_total)

        assert row == "cust_1,99.99,5"

    def test_to_csv_row_formatting(self):
        """Test that amount is formatted with 2 decimal places."""
        customer_total = CustomerTotalSchema(
            customer_id="cust_2", total_amount=100.1, order_count=1
        )
        row = OrderTransformer.to_csv_row(customer_total)

        assert row == "cust_2,100.10,1"

    def test_generate_csv_content(self):
        """Test generation of complete CSV content."""
        results = [
            CustomerTotalSchema(
                customer_id="cust_1", total_amount=100.0, order_count=2
            ),
            CustomerTotalSchema(
                customer_id="cust_2", total_amount=50.50, order_count=1
            ),
        ]

        csv_content = OrderTransformer.generate_csv_content(results)
        lines = csv_content.split("\n")

        assert len(lines) == 3
        assert lines[0] == "customer_id,total_amount,order_count"
        assert lines[1] == "cust_1,100.00,2"
        assert lines[2] == "cust_2,50.50,1"

    def test_generate_csv_content_empty(self):
        """Test CSV generation with empty results."""
        results = []
        csv_content = OrderTransformer.generate_csv_content(results)

        assert csv_content == "customer_id,total_amount,order_count"
