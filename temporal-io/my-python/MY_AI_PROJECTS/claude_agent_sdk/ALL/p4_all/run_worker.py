"""Worker for Product Launch Automation."""

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from shared.config import config

from .workflow import ProductLaunchWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Run the worker for product launch workflows."""

    # Connect to Temporal server
    client = await Client.connect(config.temporal.host, namespace=config.temporal.namespace)

    # Create worker
    worker = Worker(
        client,
        task_queue="product-launch-queue",
        workflows=[ProductLaunchWorkflow],
        activities=[],  # Activities would be added here in full implementation
    )

    logger.info("Worker started for product launch automation")
    logger.info(f"Task queue: product-launch-queue")
    logger.info(f"Temporal server: {config.temporal.host}")
    logger.info("")
    logger.info("NOTE: This is a demonstration workflow structure.")
    logger.info("Implement full activities for production use.")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
