"""
Worker Script - Human in the Loop
Runs the Temporal worker that processes expense approval workflows.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker

from workflow_definitions import (
    ExpenseApprovalWorkflow,
    notify_approver,
    notify_employee,
    process_approved_expense,
    validate_expense,
)

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "1-basic-human-in-loop-task-queue"
MAX_CONCURRENT_ACTIVITIES = 5


async def main():
    """Start and run the worker."""
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)
    print(f"Connected to Temporal at {TEMPORAL_HOST}")

    # Create and run worker
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ExpenseApprovalWorkflow],
        activities=[
            validate_expense,
            notify_approver,
            process_approved_expense,
            notify_employee,
        ],
        activity_executor=ThreadPoolExecutor(MAX_CONCURRENT_ACTIVITIES),
    )

    print(f"Worker started on task queue: {TASK_QUEUE}")
    print(f"Max concurrent activities: {MAX_CONCURRENT_ACTIVITIES}")
    print("Registered workflows:")
    print("  - ExpenseApprovalWorkflow (with signals and queries)")
    print("Registered activities:")
    print("  - validate_expense, notify_approver, process_approved_expense, notify_employee")
    print("Press Ctrl+C to stop the worker")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
