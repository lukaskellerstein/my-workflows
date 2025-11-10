"""
Example: Child Workflow
This demonstrates how to use child workflows for modular, reusable workflow components.
Parent workflow delegates subtasks to child workflows.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from typing import List

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


@dataclass
class OrderItem:
    product: str
    quantity: int
    price: float


@dataclass
class Order:
    order_id: str
    customer: str
    items: List[OrderItem]


# Activities for processing orders


@activity.defn
def validate_inventory(item: OrderItem) -> bool:
    activity.logger.info(f"Validating inventory for {item.product}")
    # Simulate inventory check
    return True


@activity.defn
def calculate_subtotal(item: OrderItem) -> float:
    activity.logger.info(f"Calculating subtotal for {item.product}")
    return item.quantity * item.price


@activity.defn
def process_payment(total_amount: float, customer: str) -> str:
    activity.logger.info(f"Processing payment of ${total_amount} for {customer}")
    # Simulate payment processing
    return f"Payment successful: ${total_amount:.2f}"


@activity.defn
def ship_order(order_id: str, customer: str) -> str:
    activity.logger.info(f"Shipping order {order_id} to {customer}")
    # Simulate shipping
    return f"Order {order_id} shipped to {customer}"


# Child Workflow: Process a single order item
@workflow.defn
class ProcessOrderItemWorkflow:
    @workflow.run
    async def run(self, item: OrderItem) -> float:
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
    @workflow.run
    async def run(self, order: Order) -> str:
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


async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker for the workflows
    async with Worker(
        client,
        task_queue="1-basic-child-workflow-task-queue",
        workflows=[ProcessOrderWorkflow, ProcessOrderItemWorkflow],
        activities=[
            validate_inventory,
            calculate_subtotal,
            process_payment,
            ship_order,
        ],
        activity_executor=ThreadPoolExecutor(10),
    ):
        # Create a sample order
        order = Order(
            order_id="ORD-12345",
            customer="John Doe",
            items=[
                OrderItem(product="Laptop", quantity=1, price=999.99),
                OrderItem(product="Mouse", quantity=2, price=29.99),
                OrderItem(product="Keyboard", quantity=1, price=79.99),
            ],
        )

        # Execute the parent workflow
        result = await client.execute_workflow(
            ProcessOrderWorkflow.run,
            order,
            id="1-basic-child-workflow-order-12345",
            task_queue="1-basic-child-workflow-task-queue",
        )
        print(f"\n{result}")


if __name__ == "__main__":
    asyncio.run(main())
