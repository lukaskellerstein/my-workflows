"""
Worker Script - Child Workflow
Runs the Temporal worker that processes parent and child workflows.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker

from workflow_definitions import (
    ProcessOrderItemWorkflow,
    ProcessOrderWorkflow,
    calculate_subtotal,
    process_payment,
    ship_order,
    validate_inventory,
)

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "1-basic-child-workflow-task-queue"
MAX_CONCURRENT_ACTIVITIES = 10


async def main():
    """Start and run the worker."""
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)
    print(f"Connected to Temporal at {TEMPORAL_HOST}")

    # Create and run worker with both parent and child workflows
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ProcessOrderWorkflow, ProcessOrderItemWorkflow],
        activities=[
            validate_inventory,
            calculate_subtotal,
            process_payment,
            ship_order,
        ],
        activity_executor=ThreadPoolExecutor(MAX_CONCURRENT_ACTIVITIES),
    )

    print(f"Worker started on task queue: {TASK_QUEUE}")
    print(f"Max concurrent activities: {MAX_CONCURRENT_ACTIVITIES}")
    print("Registered workflows:")
    print("  - ProcessOrderWorkflow (parent)")
    print("  - ProcessOrderItemWorkflow (child)")
    print("Registered activities:")
    print("  - validate_inventory, calculate_subtotal, process_payment, ship_order")
    print("Press Ctrl+C to stop the worker")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
