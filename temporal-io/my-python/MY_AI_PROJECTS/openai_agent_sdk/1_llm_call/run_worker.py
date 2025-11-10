"""Worker for Content Publishing Pipeline."""

import asyncio
import os
from dotenv import load_dotenv

from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from workflows import ContentPublishingWorkflow
from activities import validate_article, process_images, assemble_publication
from activities.llm_activities import analyze_content, optimize_seo


async def main():
    """Run the Temporal worker."""
    # Load environment variables
    load_dotenv()

    # Ensure OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable must be set")

    # Connect to Temporal server
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(
        temporal_address,
        plugins=[OpenAIAgentsPlugin()],
    )

    # Create worker
    worker = Worker(
        client,
        task_queue="content-publishing-task-queue",
        workflows=[ContentPublishingWorkflow],
        activities=[
            validate_article,
            analyze_content,
            optimize_seo,
            process_images,
            assemble_publication,
        ],
    )

    print("Starting Content Publishing Worker...")
    print(f"Connected to Temporal at {temporal_address}")
    print("Task queue: content-publishing-task-queue")
    print("\nWaiting for workflow tasks...")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
