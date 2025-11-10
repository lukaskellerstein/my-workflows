"""Temporal worker for marketing campaigns."""

import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from user_actor_workflow import UserActorWorkflow
from campaign_workflow import CampaignWorkflow
from activities import (
    send_email,
    send_sms,
    send_push_notification,
    send_in_app_message,
    send_message,
    log_analytics_event,
)


async def main():
    """Run the worker."""
    # Connect to Temporal server
    client = await Client.connect("localhost:7233")

    # Create worker
    worker = Worker(
        client,
        task_queue="marketing-campaign-queue",
        workflows=[UserActorWorkflow, CampaignWorkflow],
        activities=[
            send_email,
            send_sms,
            send_push_notification,
            send_in_app_message,
            send_message,
            log_analytics_event,
        ],
    )

    print("🚀 Marketing Campaign Worker started!")
    print("📋 Task Queue: marketing-campaign-queue")
    print("👤 Workflows: UserActorWorkflow, CampaignWorkflow")
    print("⏳ Waiting for workflows...")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
