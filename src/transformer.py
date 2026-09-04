"""Data transformation logic for aggregating orders by customer."""

from typing import Dict, List, Tuple, Any
from src.schema import OrderSchema, CustomerTotalSchema
from src.logger import setup_logger

logger = setup_logger(__name__)


class OrderTransformer:
    """Transforms order records into customer totals."""

    @staticmethod
    def aggregate_by_customer(
        orders: List[OrderSchema],
    ) -> Tuple[List[CustomerTotalSchema], Dict[str, Any]]:
        """Aggregate orders by customer_id to calculate totals and counts.

        Args:
            orders: List of validated order records

        Returns:
            Tuple of (aggregated results, metrics)
        """
        # Aggregate in-memory using dictionary
        aggregates: Dict[str, Dict[str, Any]] = {}

        for order in orders:
            if order.customer_id not in aggregates:
                aggregates[order.customer_id] = {
                    "total_amount": 0.0,
                    "order_count": 0,
                }

            aggregates[order.customer_id]["total_amount"] += order.amount
            aggregates[order.customer_id]["order_count"] += 1

        # Convert to output schema
        results = [
            CustomerTotalSchema(
                customer_id=customer_id,
                total_amount=data["total_amount"],
                order_count=data["order_count"],
            )
            for customer_id, data in sorted(aggregates.items())
        ]

        metrics = {
            "unique_customers": len(results),
            "total_orders_aggregated": len(orders),
            "total_amount": sum(r.total_amount for r in results),
        }

        logger.info(
            f"Aggregated {len(orders)} orders from {len(results)} unique customers"
        )

        return results, metrics

    @staticmethod
    def to_csv_row(customer_total: CustomerTotalSchema) -> str:
        """Convert customer total to CSV row.

        Args:
            customer_total: CustomerTotalSchema instance

        Returns:
            CSV row as string
        """
        return (
            f"{customer_total.customer_id},"
            f"{customer_total.total_amount:.2f},"
            f"{customer_total.order_count}"
        )

    @staticmethod
    def generate_csv_content(results: List[CustomerTotalSchema]) -> str:
        """Generate complete CSV content with headers.

        Args:
            results: List of customer totals

        Returns:
            CSV content as string
        """
        lines = ["customer_id,total_amount,order_count"]

        for result in results:
            lines.append(OrderTransformer.to_csv_row(result))

        return "\n".join(lines)
