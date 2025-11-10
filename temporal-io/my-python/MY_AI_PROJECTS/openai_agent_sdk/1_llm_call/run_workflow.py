"""Client to execute Content Publishing Workflow."""

import asyncio
import os
from dotenv import load_dotenv

from temporalio.client import Client
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin
from temporalio.common import (
    TypedSearchAttributes,
    SearchAttributeKey,
    SearchAttributePair,
)


import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from workflows import ContentPublishingWorkflow
from models import ArticleInput


# Define search attribute key for tagging workflows
ai_agent_type = SearchAttributeKey.for_text("AIAgentType")


async def main():
    """Execute the content publishing workflow."""
    # Load environment variables
    load_dotenv()

    # Connect to Temporal server
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(
        temporal_address,
        plugins=[OpenAIAgentsPlugin()],
    )

    # Create sample article
    article = ArticleInput(
        title="The Future of AI-Powered Development Tools",
        author="Jane Developer",
        format="markdown",
        tags=["AI", "development", "automation", "productivity"],
        content="""
# The Future of AI-Powered Development Tools

Artificial intelligence is revolutionizing the way developers write code, debug applications,
and manage projects. In this article, we'll explore the emerging trends and technologies
that are shaping the future of software development.

## Understanding AI Assistants

Modern AI coding assistants like GitHub Copilot, Amazon CodeWhisperer, and others have
transformed the development landscape. These tools leverage large language models to provide
intelligent code suggestions, auto-completion, and even generate entire functions based on
natural language descriptions.

The impact on developer productivity has been significant. Studies show that developers using
AI assistants can complete tasks 30-50% faster, with the quality of code remaining comparable
to manually written code.

## Workflow Orchestration

Tools like Temporal.io are enabling developers to build reliable, scalable distributed systems
with ease. By combining AI capabilities with durable workflow execution, teams can create
sophisticated automation pipelines that handle complex business logic while maintaining
resilience to failures.

## The Path Forward

As AI models continue to improve and become more specialized for software development tasks,
we can expect even greater integration between AI assistants and traditional development tools.
The future likely holds:

- More sophisticated code generation capabilities
- Better understanding of project context and architecture
- Automated testing and bug detection
- Intelligent refactoring suggestions
- Natural language interfaces for complex operations

## Conclusion

The integration of AI into development workflows represents a fundamental shift in how
software is created. While AI won't replace developers, it will augment their capabilities
and allow them to focus on higher-level problem-solving and creative solutions.

The key is finding the right balance between leveraging AI assistance and maintaining
control over the development process. Tools that provide transparency, allow customization,
and integrate seamlessly into existing workflows will be the winners in this space.

![AI Development](https://example.com/images/ai-development.jpg)
""",
    )

    print("=" * 80)
    print("Content Publishing Pipeline - Workflow Execution")
    print("=" * 80)
    print(f"\nArticle: {article.title}")
    print(f"Author: {article.author}")
    print(f"Format: {article.format}")
    print(f"Tags: {', '.join(article.tags)}")
    print(f"\nExecuting workflow...")

    # Execute workflow
    result = await client.execute_workflow(
        ContentPublishingWorkflow.run,
        article,
        id=f"content-publish-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        task_queue="content-publishing-task-queue",
        search_attributes=TypedSearchAttributes(
            [SearchAttributePair(ai_agent_type, "OpenAIAgentSDK")]
        ),
    )

    # Display results
    print("\n" + "=" * 80)
    print("Publication Complete!")
    print("=" * 80)
    print(f"\nPublication ID: {result.publication_id}")
    print(f"Publication URL: {result.publication_url}")
    print(f"\nMetadata:")
    print(f"  Word Count: {result.metadata['word_count']}")
    print(f"  Tone: {result.metadata['tone']}")
    print(f"  Readability: {result.metadata['readability']}")
    print(f"  Topics: {', '.join(result.metadata['topics'])}")
    if result.metadata["sensitive_topics"]:
        print(f"  Sensitive Topics: {', '.join(result.metadata['sensitive_topics'])}")

    print(f"\nSEO Optimization:")
    print(f"  Meta Description: {result.seo.meta_description}")
    print(f"  Keywords: {', '.join(result.seo.keywords)}")
    print(f"  Alternative Titles:")
    for i, title in enumerate(result.seo.title_alternatives, 1):
        print(f"    {i}. {title}")
    if result.seo.internal_links:
        print(f"  Suggested Internal Links: {', '.join(result.seo.internal_links)}")

    print(f"\nImages Processed: {len(result.images)}")
    for img in result.images:
        print(f"  - {img.original_path} -> {len(img.optimized_paths)} variants")

    print(f"\nPublished at: {result.timestamp}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
