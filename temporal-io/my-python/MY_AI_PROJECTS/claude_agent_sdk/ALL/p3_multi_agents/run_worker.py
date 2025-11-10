"""Worker for Code Review Pipeline."""

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from shared.config import config

from .activities import (
    execute_generated_tests,
    generate_review_report,
    multi_agent_code_review,
    send_notifications,
    validate_code_submission,
)
from .workflow import CodeReviewWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Run the worker for code review workflows."""

    # Connect to Temporal server
    client = await Client.connect(config.temporal.host, namespace=config.temporal.namespace)

    # Create worker
    worker = Worker(
        client,
        task_queue="code-review-queue",
        workflows=[CodeReviewWorkflow],
        activities=[
            validate_code_submission,
            multi_agent_code_review,
            execute_generated_tests,
            generate_review_report,
            send_notifications,
        ],
    )

    logger.info("Worker started for code review pipeline")
    logger.info(f"Task queue: code-review-queue")
    logger.info(f"Temporal server: {config.temporal.host}")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
