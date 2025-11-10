"""Main runner for Content Publishing Workflow (Project 1)."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from temporalio.client import Client
from temporalio.worker import Worker

# Import workflow and activities
from workflows.content_publishing import ContentPublishingWorkflow
from activities.deterministic.validation import ArticleInput, validate_article
from activities.deterministic.image_processing import process_images
from activities.deterministic.publication import assemble_and_publish
from activities.llm_activities.content_analysis import analyze_content
from activities.llm_activities.seo_optimization import optimize_seo


async def run_worker():
    """Run the Temporal worker for content publishing."""
    client = await Client.connect("localhost:7233")

    # Create worker
    worker = Worker(
        client,
        task_queue="content-publishing-queue",
        workflows=[ContentPublishingWorkflow],
        activities=[
            validate_article,
            analyze_content,
            optimize_seo,
            process_images,
            assemble_and_publish,
        ],
        activity_executor=ThreadPoolExecutor(max_workers=10),
    )

    print("Content Publishing Worker started. Press Ctrl+C to exit.")
    await worker.run()


async def run_workflow():
    """Execute a sample workflow."""
    client = await Client.connect("localhost:7233")

    # Create sample article
    sample_article = ArticleInput(
        title="The Future of Artificial Intelligence in Content Creation",
        content="""
        Artificial intelligence is transforming the landscape of content creation in unprecedented ways.
        Modern AI systems can now assist writers, editors, and content creators throughout the entire
        publishing pipeline, from initial ideation to final publication.

        The integration of large language models (LLMs) into content workflows has enabled several
        breakthrough capabilities. First, these systems can analyze content for tone, readability, and
        audience appropriateness with remarkable accuracy. Second, they can generate SEO-optimized
        metadata, including titles, descriptions, and keywords that help content reach wider audiences.

        However, the human element remains crucial. While AI can optimize and enhance content, the
        creative vision, original insights, and authentic voice still come from human creators. The
        most successful content strategies combine AI's analytical power with human creativity and judgment.

        Looking ahead, we can expect even deeper integration between AI tools and content management
        systems. Automated workflows will handle routine optimization tasks, freeing creators to focus
        on what they do best: telling compelling stories and sharing unique perspectives.

        The key is finding the right balance—using AI as a powerful assistant while maintaining the
        human touch that makes content truly engaging and valuable to readers.
        """,
        format="markdown",
        author="AI Researcher",
        tags=["AI", "content creation", "technology", "future"],
    )

    # Execute workflow
    result = await client.execute_workflow(
        ContentPublishingWorkflow.run,
        sample_article,
        id=f"content-publishing-{sample_article.title[:20]}",
        task_queue="content-publishing-queue",
    )

    print("\n" + "=" * 80)
    print("CONTENT PUBLISHING WORKFLOW COMPLETED")
    print("=" * 80)
    print(f"\nArticle ID: {result.article_id}")
    print(f"Title: {result.title}")
    print(f"Publication URL: {result.publication_url}")
    print(f"Published At: {result.published_at}")
    print(f"Status: {result.status}")
    print(f"\nSEO Metadata:")
    print(f"  Keywords: {', '.join(result.metadata['seo']['keywords'][:5])}")
    print(f"  Topics: {', '.join(result.metadata['seo']['topics'][:5])}")
    print(f"\nImages: {result.metadata['images']['count']} processed")
    print("=" * 80)


async def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        await run_worker()
    else:
        await run_workflow()


if __name__ == "__main__":
    asyncio.run(main())
