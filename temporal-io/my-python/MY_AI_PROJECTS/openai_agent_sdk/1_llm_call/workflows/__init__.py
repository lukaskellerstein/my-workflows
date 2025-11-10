"""Content Publishing Pipeline Workflow."""

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from models import ArticleInput, PublicationManifest
    from activities import (
        validate_article,
        process_images,
        assemble_publication,
    )
    from activities.llm_activities import (
        analyze_content,
        optimize_seo,
    )


@workflow.defn
class ContentPublishingWorkflow:
    """
    Content Publishing Pipeline demonstrating deterministic and LLM activities.

    Workflow Steps:
    1. Validate article format and metadata (deterministic)
    2. Analyze content with LLM (tone, readability, topics)
    3. Optimize SEO with LLM (titles, meta description, keywords)
    4. Process images (deterministic)
    5. Assemble final publication package (deterministic)
    """

    @workflow.run
    async def run(self, article: ArticleInput) -> PublicationManifest:
        """Execute the content publishing pipeline."""

        workflow.logger.info(f"Starting content publishing workflow for: {article.title}")

        # Step 1: Validate article (deterministic)
        validation = await workflow.execute_activity(
            validate_article,
            article,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not validation.is_valid:
            error_msg = f"Article validation failed: {', '.join(validation.errors)}"
            workflow.logger.error(error_msg)
            raise ValueError(error_msg)

        workflow.logger.info(
            f"Article validated: {validation.word_count} words, "
            f"format: {validation.metadata['format']}"
        )

        # Step 2: Analyze content with LLM
        # Use retry policy for LLM calls to handle transient failures
        llm_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        analysis = await workflow.execute_activity(
            analyze_content,
            args=[article, validation.word_count],
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=llm_retry_policy,
        )

        workflow.logger.info(
            f"Content analyzed - Tone: {analysis.tone}, "
            f"Readability: {analysis.readability_score}, "
            f"Topics: {', '.join(analysis.topics[:3])}"
        )

        # Step 3: Optimize SEO with LLM
        seo = await workflow.execute_activity(
            optimize_seo,
            args=[article, analysis],
            start_to_close_timeout=timedelta(seconds=120),  # Increased timeout
            retry_policy=llm_retry_policy,
        )

        workflow.logger.info(
            f"SEO optimized - {len(seo.title_alternatives)} title alternatives, "
            f"{len(seo.keywords)} keywords"
        )

        # Step 4: Process images (deterministic)
        images = await workflow.execute_activity(
            process_images,
            article.content,
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info(f"Processed {len(images)} images")

        # Step 5: Assemble publication (deterministic)
        manifest = await workflow.execute_activity(
            assemble_publication,
            args=[article, validation, analysis, seo, images],
            start_to_close_timeout=timedelta(seconds=30),
        )

        workflow.logger.info(
            f"Publication complete: {manifest.publication_url} "
            f"(ID: {manifest.publication_id})"
        )

        return manifest
