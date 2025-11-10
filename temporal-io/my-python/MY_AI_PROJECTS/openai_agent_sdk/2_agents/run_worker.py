"""Worker for Research Assistant Workflow."""

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

from workflows import ResearchAssistantWorkflow
from activities import (
    query_context_from_mongodb,
    store_sources_in_mongodb,
    enrich_and_deduplicate,
    store_knowledge_graph,
    store_research_session,
)
from activities.agent_activities import (
    research_web_sources,
    research_academic_sources,
    build_knowledge_graph,
    synthesize_research,
    generate_audio_report,
)


async def main():
    """Run the Temporal worker."""
    # Load environment variables
    load_dotenv()

    # Ensure required environment variables are set
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable must be set")

    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")

    # Connect to Temporal server
    client = await Client.connect(
        temporal_address,
        plugins=[OpenAIAgentsPlugin()],
    )

    # Create worker
    worker = Worker(
        client,
        task_queue="research-assistant-task-queue",
        workflows=[ResearchAssistantWorkflow],
        activities=[
            # MongoDB and deterministic activities
            query_context_from_mongodb,
            store_sources_in_mongodb,
            enrich_and_deduplicate,
            store_knowledge_graph,
            store_research_session,
            # AI agent activities
            research_web_sources,
            research_academic_sources,
            build_knowledge_graph,
            synthesize_research,
            generate_audio_report,
        ],
    )

    print("=" * 80)
    print("Starting Research Assistant Worker")
    print("=" * 80)
    print(f"Temporal Server: {temporal_address}")
    print(f"MongoDB URI: {mongodb_uri}")
    print("Task queue: research-assistant-task-queue")
    print("\nAI Agents:")
    print("  - Web Research Agent (with Tavily MCP)")
    print("  - Academic Research Agent (with arXiv MCP)")
    print("  - Knowledge Graph Builder")
    print("  - Research Synthesis Agent")
    print("  - Audio Report Generator (with ElevenLabs + MinIO MCP)")
    print("\nWaiting for workflow tasks...")
    print("=" * 80)

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
