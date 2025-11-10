"""
Workflow Starter Script - Child Workflow
Simple Python script to start order processing workflows.
"""
import asyncio
import uuid

from temporalio.client import Client

from workflow_definitions import Order, OrderItem, ProcessOrderWorkflow

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "1-basic-child-workflow-task-queue"


async def start_workflow(order: Order, workflow_id: str = None) -> str:
    """
    Start a new order processing workflow.

    Args:
        order: The order to process
        workflow_id: Optional workflow ID (auto-generated if not provided)

    Returns:
        The workflow result message
    """
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)

    # Generate workflow ID if not provided
    if workflow_id is None:
        workflow_id = f"child-workflow-order-{uuid.uuid4()}"

    print(f"Starting workflow with ID: {workflow_id}")
    print(f"Order ID: {order.order_id}")
    print(f"Customer: {order.customer}")
    print(f"Items: {len(order.items)}")

    # Start and wait for workflow completion
    result = await client.execute_workflow(
        ProcessOrderWorkflow.run,
        order,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    print(f"\n{result}")
    return result


async def main():
    """Main entry point."""
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

    await start_workflow(order)


if __name__ == "__main__":
    asyncio.run(main())
