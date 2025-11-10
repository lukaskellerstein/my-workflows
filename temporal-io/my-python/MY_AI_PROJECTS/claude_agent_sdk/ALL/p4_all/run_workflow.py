"""Starter script for Product Launch Automation."""

import asyncio
import logging
from datetime import datetime, timedelta

from temporalio.client import Client
from temporalio.common import TypedSearchAttributes, SearchAttributeKey, SearchAttributePair

from shared.config import config
from shared.models import ProductSpecification

from .workflow import ProductLaunchWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define search attribute key for tagging workflows
ai_agent_type = SearchAttributeKey.for_text("AIAgentType")


async def main() -> None:
    """Start a product launch workflow."""

    # Connect to Temporal server
    client = await Client.connect(config.temporal.host, namespace=config.temporal.namespace)

    # Product specification
    product_spec = ProductSpecification(
        product_id="prod-ai-assistant-001",
        name="AI Code Assistant Pro",
        description="Next-generation AI-powered code completion and review tool",
        target_audience=["developers", "tech-leads", "enterprises"],
        key_features=[
            "Real-time code completion",
            "Intelligent code review",
            "Multi-language support",
            "Team collaboration",
            "Security scanning",
        ],
        launch_date=datetime.now() + timedelta(days=30),
        budget=50000.0,
    )

    # Start workflow
    workflow_id = f"product-launch-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    logger.info(f"Starting product launch workflow: {workflow_id}")
    logger.info(f"Product: {product_spec.name}")
    logger.info(f"Launch Date: {product_spec.launch_date.strftime('%Y-%m-%d')}")

    result = await client.execute_workflow(
        ProductLaunchWorkflow.run,
        product_spec,
        id=workflow_id,
        task_queue="product-launch-queue",
        search_attributes=TypedSearchAttributes(
            [SearchAttributePair(ai_agent_type, "ClaudeAgentSDK")]
        ),
    )

    logger.info("=" * 80)
    logger.info("PRODUCT LAUNCH WORKFLOW COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Product ID: {result['product_id']}")
    logger.info(f"Product Name: {result['product_name']}")
    logger.info(f"Launch Date: {result['launch_date']}")
    logger.info(f"Status: {result['status']}")
    logger.info("")
    logger.info(f"Note: {result['message']}")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
