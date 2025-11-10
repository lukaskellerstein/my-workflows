"""
Worker Script - Multiple Nodes
Runs the Temporal worker that processes multiple-node workflow and activity tasks.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker

from workflow_definitions import (
    MultipleNodesWorkflow,
    save_result,
    transform_data,
    validate_input,
)

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "0-simple-multiple-nodes-task-queue"
MAX_CONCURRENT_ACTIVITIES = 10


async def main():
    """Start and run the worker."""
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)
    print(f"Connected to Temporal at {TEMPORAL_HOST}")

    # Create and run worker
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[MultipleNodesWorkflow],
        activities=[validate_input, transform_data, save_result],
        activity_executor=ThreadPoolExecutor(MAX_CONCURRENT_ACTIVITIES),
    )

    print(f"Worker started on task queue: {TASK_QUEUE}")
    print(f"Max concurrent activities: {MAX_CONCURRENT_ACTIVITIES}")
    print("Registered activities: validate_input, transform_data, save_result")
    print("Press Ctrl+C to stop the worker")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
