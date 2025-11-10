"""Starter script for Content Publishing Pipeline."""

import asyncio
import logging
from datetime import datetime

from temporalio.client import Client
from temporalio.common import TypedSearchAttributes, SearchAttributeKey, SearchAttributePair

from shared.config import config
from shared.models import ArticleInput, ContentFormat

from .workflow import ContentPublishingWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define search attribute key for tagging workflows
ai_agent_type = SearchAttributeKey.for_text("AIAgentType")


async def main() -> None:
    """Start a content publishing workflow."""

    # Connect to Temporal server
    client = await Client.connect(config.temporal.host, namespace=config.temporal.namespace)

    # Sample article input
    article = ArticleInput(
        title="The Future of AI-Powered Development Tools",
        content="""
        Artificial Intelligence is revolutionizing the way developers work. From code completion
        to automated testing, AI-powered tools are becoming indispensable in modern software
        development workflows.

        Code assistants like GitHub Copilot and Claude Code are transforming how we write code.
        These tools leverage large language models to understand context and provide intelligent
        suggestions that go far beyond simple autocomplete.

        The integration of AI into development workflows extends beyond just writing code. Tools
        now help with code review, identifying potential bugs, suggesting optimizations, and even
        generating comprehensive test suites. This allows developers to focus on higher-level
        problem-solving while AI handles many routine tasks.

        Security is another area where AI is making significant impact. AI-powered static analysis
        tools can detect vulnerabilities that might be missed by traditional scanners. They
        understand code patterns and can identify subtle security issues across large codebases.

        Looking ahead, we can expect even deeper integration of AI into development environments.
        Natural language interfaces may allow developers to express intent in plain language,
        with AI translating that into working code. The line between human creativity and AI
        assistance will continue to blur, creating powerful hybrid workflows.

        However, challenges remain. Developers must learn to effectively collaborate with AI tools,
        understanding their strengths and limitations. Code quality, maintainability, and security
        cannot be fully delegated to AI - human oversight remains crucial.

        The future of software development is collaborative, with AI serving as an intelligent
        partner that amplifies human capabilities rather than replacing them.
        """,
        format=ContentFormat.MARKDOWN,
        author="Alex Johnson",
        metadata={
            "category": "Technology",
            "tags": ["AI", "Development", "Productivity", "Tools"],
            "priority": "high",
        },
    )

    # Start workflow
    workflow_id = f"content-publish-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    logger.info(f"Starting workflow: {workflow_id}")
    logger.info(f"Article: {article.title}")

    result = await client.execute_workflow(
        ContentPublishingWorkflow.run,
        article,
        id=workflow_id,
        task_queue="content-publishing-queue",
        search_attributes=TypedSearchAttributes(
            [SearchAttributePair(ai_agent_type, "ClaudeAgentSDK")]
        ),
    )

    logger.info("=" * 80)
    logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info(f"Article ID: {result.article_id}")
    logger.info(f"Publication URL: {result.publication_url}")
    logger.info(f"Published At: {result.published_at}")
    logger.info(f"Optimized Title: {result.metadata.get('optimized_title')}")
    logger.info(f"Keywords: {', '.join(result.metadata.get('keywords', []))}")
    logger.info(f"Readability Score: {result.metadata.get('readability_score')}")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
