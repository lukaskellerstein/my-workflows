"""Workflow for Content Publishing Pipeline."""

import logging
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from shared.models import ArticleInput, PublishedArticle, ValidationStatus
    from .activities import ContentPublishingActivities

logger = logging.getLogger(__name__)


@workflow.defn
class ContentPublishingWorkflow:
    """
    Workflow orchestrating the content publishing pipeline.

    Steps:
    1. Validate input (deterministic)
    2. Analyze content with LLM
    3. Optimize for SEO with LLM
    4. Process images (deterministic)
    5. Assemble and publish (deterministic)
    """

    @workflow.run
    async def run(self, article: ArticleInput) -> PublishedArticle:
        """Execute the content publishing workflow."""

        workflow.logger.info(f"Starting content publishing workflow for: {article.title}")

        # Step 1: Validate input (deterministic, short timeout)
        validation_result = await workflow.execute_activity_method(
            ContentPublishingActivities.validate_article_input,
            article,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if validation_result.status == ValidationStatus.INVALID:
            error_msg = f"Article validation failed: {', '.join(validation_result.errors)}"
            workflow.logger.error(error_msg)
            raise ValueError(error_msg)

        workflow.logger.info("Article validation passed")

        # Step 2: Analyze content with LLM (with retry policy)
        llm_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        content_analysis = await workflow.execute_activity_method(
            ContentPublishingActivities.analyze_content_with_llm,
            article,
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=llm_retry_policy,
        )

        workflow.logger.info(f"Content analysis complete: {content_analysis.tone}")

        # Step 3: Optimize for SEO with LLM (with retry policy)
        seo_optimization = await workflow.execute_activity_method(
            ContentPublishingActivities.optimize_for_seo,
            args=[article, content_analysis],
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=llm_retry_policy,
        )

        workflow.logger.info(
            f"SEO optimization complete: {len(seo_optimization.keywords)} keywords"
        )

        # Step 4: Process images (deterministic)
        processed_images = await workflow.execute_activity_method(
            ContentPublishingActivities.process_images,
            article,
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info(
            f"Image processing complete: {len(processed_images.get('original', []))} images"
        )

        # Step 5: Assemble and publish (deterministic)
        published_article = await workflow.execute_activity_method(
            ContentPublishingActivities.assemble_and_publish,
            args=[article, content_analysis, seo_optimization, processed_images],
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info(f"Article published: {published_article.publication_url}")

        return published_article
