"""Starter script for Research Assistant Workflow."""

import asyncio
import logging
from datetime import datetime

from temporalio.client import Client
from temporalio.common import (
    TypedSearchAttributes,
    SearchAttributeKey,
    SearchAttributePair,
)

from shared.config import config
from main_workflow import ResearchAssistantWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define search attribute key for tagging workflows
ai_agent_type = SearchAttributeKey.for_text("AIAgentType")


async def main() -> None:
    """Start a research assistant workflow."""

    # Connect to Temporal server
    client = await Client.connect(
        config.temporal.host, namespace=config.temporal.namespace
    )

    # Research query
    query = "What are the latest methods for benchmarking and evaluating AI agents, and how can we measure whether changes—such as modifying the system message—improve or degrade an agent’s performance across different tasks?"

    # Start workflow
    workflow_id = f"research-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    logger.info(f"Starting research assistant workflow: {workflow_id}")
    logger.info(f"Query: {query}")

    result = await client.execute_workflow(
        ResearchAssistantWorkflow.run,
        query,
        id=workflow_id,
        task_queue="research-assistant-queue",
        search_attributes=TypedSearchAttributes(
            [SearchAttributePair(ai_agent_type, "ClaudeAgentSDK")]
        ),
    )

    logger.info("=" * 80)
    logger.info("RESEARCH ASSISTANT WORKFLOW COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Run ID: {result['run_id']}")
    logger.info(f"Total Sources: {result['statistics']['total_sources']}")
    logger.info(f"  - Web Sources: {result['web_sources_count']}")
    logger.info(f"  - Academic Papers: {result['academic_sources_count']}")
    logger.info(f"Knowledge Graph Nodes: {result['knowledge_graph_nodes']}")
    logger.info("")
    logger.info("Audio Report:")
    logger.info(f"  - Report ID: {result['audio_report_id']}")
    logger.info(f"  - Text Report (MinIO): {result.get('text_minio_url', 'N/A')}")
    if result.get("audio_generation_success"):
        logger.info(f"  - Audio File (MinIO): {result.get('audio_minio_url', 'N/A')}")
        logger.info(f"  - Status: ✓ Audio successfully generated and uploaded to MinIO")
    else:
        logger.info(f"  - Status: ✗ Audio generation failed")
    logger.info("")
    logger.info("Main Findings:")
    for i, finding in enumerate(result.get("main_findings", [])[:5], 1):
        logger.info(f"  {i}. {finding}")
    logger.info("")
    logger.info("Knowledge Gaps:")
    for gap in result.get("knowledge_gaps", [])[:3]:
        logger.info(f"  - {gap}")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
