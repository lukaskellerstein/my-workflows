"""Temporal worker for HR approval workflow."""

import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from workflows import HRApprovalWorkflow
from activities import (
    send_slack_notification,
    send_approval_notification,
    notify_employee,
    record_approval,
    provision_resource,
)


async def main():
    """Run the worker."""
    # Connect to Temporal server
    client = await Client.connect("localhost:7233")

    # Create worker
    worker = Worker(
        client,
        task_queue="hr-approval-queue",
        workflows=[HRApprovalWorkflow],
        activities=[
            send_slack_notification,
            send_approval_notification,
            notify_employee,
            record_approval,
            provision_resource,
        ],
    )

    print("🚀 HR Approval Worker started!")
    print("📋 Task Queue: hr-approval-queue")
    print("⏳ Waiting for workflows...")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
