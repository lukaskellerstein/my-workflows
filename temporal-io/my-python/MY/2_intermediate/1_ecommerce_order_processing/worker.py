"""Temporal worker for order processing."""

import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from workflows import OrderProcessingWorkflow
from activities import (
    reserve_inventory,
    process_payment,
    prepare_shipment,
    ship_order,
    send_email_notification,
    release_inventory,
    refund_payment,
)


async def main():
    """Run the worker."""
    # Connect to Temporal server
    client = await Client.connect("localhost:7233")

    # Create worker
    worker = Worker(
        client,
        task_queue="order-processing-queue",
        workflows=[OrderProcessingWorkflow],
        activities=[
            reserve_inventory,
            process_payment,
            prepare_shipment,
            ship_order,
            send_email_notification,
            release_inventory,
            refund_payment,
        ],
    )

    print("🚀 Order Processing Worker started!")
    print("📋 Task Queue: order-processing-queue")
    print("⏳ Waiting for workflows...")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
