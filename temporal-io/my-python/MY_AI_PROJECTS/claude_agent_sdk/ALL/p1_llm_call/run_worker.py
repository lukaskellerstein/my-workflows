"""Worker for Content Publishing Pipeline."""

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from shared.config import config
from .activities import ContentPublishingActivities
from .workflow import ContentPublishingWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Run the worker for content publishing workflows."""

    # Connect to Temporal server
    client = await Client.connect(config.temporal.host, namespace=config.temporal.namespace)

    # Create activities instance
    activities = ContentPublishingActivities()

    # Create worker
    worker = Worker(
        client,
        task_queue="content-publishing-queue",
        workflows=[ContentPublishingWorkflow],
        activities=[
            activities.validate_article_input,
            activities.analyze_content_with_llm,
            activities.optimize_for_seo,
            activities.process_images,
            activities.assemble_and_publish,
        ],
    )

    logger.info("Worker started for content publishing pipeline")
    logger.info(f"Task queue: content-publishing-queue")
    logger.info(f"Temporal server: {config.temporal.host}")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
