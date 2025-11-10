"""
Workflow and Activity Definitions - Child Workflow
Demonstrates parent workflow delegating subtasks to child workflows.
"""
from dataclasses import dataclass
from datetime import timedelta
from typing import List

from temporalio import activity, workflow


@dataclass
class OrderItem:
    """Represents a single item in an order."""

    product: str
    quantity: int
    price: float


@dataclass
class Order:
    """Represents a complete order with multiple items."""

    order_id: str
    customer: str
    items: List[OrderItem]


# Activities for processing orders


@activity.defn
def validate_inventory(item: OrderItem) -> bool:
    """Validate that the item is in stock."""
    activity.logger.info(f"Validating inventory for {item.product}")
    # Simulate inventory check - always returns True in this example
    return True


@activity.defn
def calculate_subtotal(item: OrderItem) -> float:
    """Calculate the subtotal for an order item."""
    activity.logger.info(f"Calculating subtotal for {item.product}")
    return item.quantity * item.price


@activity.defn
def process_payment(total_amount: float, customer: str) -> str:
    """Process payment for the order."""
    activity.logger.info(f"Processing payment of ${total_amount} for {customer}")
    # Simulate payment processing
    return f"Payment successful: ${total_amount:.2f}"


@activity.defn
def ship_order(order_id: str, customer: str) -> str:
    """Ship the order to the customer."""
    activity.logger.info(f"Shipping order {order_id} to {customer}")
    # Simulate shipping
    return f"Order {order_id} shipped to {customer}"


# Child Workflow: Process a single order item
@workflow.defn
class ProcessOrderItemWorkflow:
    """
    Child workflow that processes a single order item.
    Validates inventory and calculates subtotal.
    """

    @workflow.run
    async def run(self, item: OrderItem) -> float:
        """Process an order item and return its subtotal."""
        workflow.logger.info(f"Processing item: {item.product}")

        # Validate inventory
        is_available = await workflow.execute_activity(
            validate_inventory,
            item,
            start_to_close_timeout=timedelta(seconds=10),
        )

        if not is_available:
            workflow.logger.warning(f"Item {item.product} not available")
            return 0.0

        # Calculate subtotal
        subtotal = await workflow.execute_activity(
            calculate_subtotal,
            item,
            start_to_close_timeout=timedelta(seconds=10),
        )

        workflow.logger.info(f"Item {item.product} processed: ${subtotal:.2f}")
        return subtotal


# Parent Workflow: Process entire order using child workflows
@workflow.defn
class ProcessOrderWorkflow:
    """
    Parent workflow that processes an entire order.
    Delegates item processing to child workflows.
    """

    @workflow.run
    async def run(self, order: Order) -> str:
        """Process an order by delegating to child workflows for each item."""
        workflow.logger.info(f"Processing order {order.order_id} for {order.customer}")

        # Process each item using child workflows
        subtotals: List[float] = []
        for item in order.items:
            workflow.logger.info(f"Starting child workflow for {item.product}")

            # Execute child workflow for each item
            subtotal = await workflow.execute_child_workflow(
                ProcessOrderItemWorkflow.run,
                item,
                id=f"{order.order_id}-item-{item.product}",
            )
            subtotals.append(subtotal)

        # Calculate total
        total_amount = sum(subtotals)
        workflow.logger.info(f"Total amount: ${total_amount:.2f}")

        # Process payment
        payment_result = await workflow.execute_activity(
            process_payment,
            args=[total_amount, order.customer],
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Ship order
        shipping_result = await workflow.execute_activity(
            ship_order,
            args=[order.order_id, order.customer],
            start_to_close_timeout=timedelta(seconds=10),
        )

        result = f"Order {order.order_id} completed:\n"
        result += f"  - {payment_result}\n"
        result += f"  - {shipping_result}\n"
        result += f"  - Items processed: {len(order.items)}"

        workflow.logger.info(f"Order {order.order_id} processing complete")
        return result
