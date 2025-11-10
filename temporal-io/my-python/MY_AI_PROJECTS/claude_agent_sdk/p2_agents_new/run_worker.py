"""Worker for Research Assistant Workflow."""

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from shared.config import config

from main_workflow import (
    ResearchAssistantWorkflow,
    adjust_memory,
    web_research_activity,
    academic_research_activity,
    enrich_and_cross_reference,
    build_knowledge_graph,
    synthesize_research,
    generate_audio_report,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Run the worker for research assistant workflows."""

    # Connect to Temporal server
    client = await Client.connect(
        config.temporal.host, namespace=config.temporal.namespace
    )

    # Create worker
    worker = Worker(
        client,
        task_queue="research-assistant-queue",
        workflows=[ResearchAssistantWorkflow],
        activities=[
            adjust_memory,
            web_research_activity,
            academic_research_activity,
            enrich_and_cross_reference,
            build_knowledge_graph,
            synthesize_research,
            generate_audio_report,
        ],
    )

    logger.info("Worker started for research assistant workflow")
    logger.info(f"Task queue: research-assistant-queue")
    logger.info(f"Temporal server: {config.temporal.host}")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
