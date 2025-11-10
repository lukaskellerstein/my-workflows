"""Content Publishing Workflow.

This workflow demonstrates integration of deterministic and LLM-powered activities
in a Temporal workflow for processing and publishing articles.
"""

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities
with workflow.unsafe.imports_passed_through():
    from ..activities.deterministic.validation import (
        ArticleInput,
        ValidationResult,
        validate_article,
    )
    from ..activities.deterministic.image_processing import (
        ImageProcessingResult,
        process_images,
    )
    from ..activities.deterministic.publication import (
        PublicationManifest,
        assemble_and_publish,
    )
    from ..activities.llm_activities.content_analysis import (
        ContentAnalysisResult,
        analyze_content,
    )
    from ..activities.llm_activities.seo_optimization import (
        SEOResult,
        optimize_seo,
    )


@workflow.defn
class ContentPublishingWorkflow:
    """
    Workflow for processing and publishing articles with AI-powered analysis and SEO.

    This workflow combines:
    - Deterministic validation and image processing
    - LLM-powered content analysis
    - LLM-powered SEO optimization
    - Deterministic publication
    """

    @workflow.run
    async def run(self, article: ArticleInput) -> PublicationManifest:
        """
        Execute the content publishing pipeline.

        Args:
            article: Article input data

        Returns:
            PublicationManifest with publication details
        """
        workflow.logger.info(f"Starting content publishing workflow for: {article.title}")

        # Generate article ID
        import hashlib

        article_id = hashlib.md5(
            f"{article.title}-{workflow.info().workflow_id}".encode()
        ).hexdigest()[:12]

        # Activity 1: Validate input (Deterministic)
        validation_result: ValidationResult = await workflow.execute_activity(
            validate_article,
            article,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not validation_result.is_valid:
            workflow.logger.error(
                f"Validation failed: {', '.join(validation_result.errors)}"
            )
            raise ValueError(f"Article validation failed: {validation_result.errors}")

        workflow.logger.info("Article validation passed")

        # Activity 2: Content Analysis (LLM Call with retry)
        llm_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
            backoff_coefficient=2.0,
        )

        content_analysis: ContentAnalysisResult = await workflow.execute_activity(
            analyze_content,
            args=[article.content, article.title],
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=llm_retry_policy,
        )

        workflow.logger.info(
            f"Content analysis completed. Tone: {content_analysis.tone}, "
            f"Topics: {len(content_analysis.key_topics)}"
        )

        # Check for sensitive topics
        if content_analysis.sensitive_topics:
            workflow.logger.warning(
                f"Sensitive topics detected: {', '.join(content_analysis.sensitive_topics)}"
            )

        # Activity 3: SEO Optimization (LLM Call with retry)
        seo_result: SEOResult = await workflow.execute_activity(
            optimize_seo,
            args=[article.content, article.title, content_analysis.key_topics],
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=llm_retry_policy,
        )

        workflow.logger.info(
            f"SEO optimization completed. Generated {len(seo_result.title_alternatives)} title alternatives"
        )

        # Activity 4: Image Processing (Deterministic)
        image_result: ImageProcessingResult = await workflow.execute_activity(
            process_images,
            args=[article.content, article_id],
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info(f"Processed {image_result.total_processed} images")

        # Activity 5: Final Assembly and Publication (Deterministic)
        # Use the best SEO title if available
        optimized_title = (
            seo_result.title_alternatives[0]
            if seo_result.title_alternatives
            else article.title
        )

        # Prepare SEO metadata
        seo_metadata = {
            "title": optimized_title,
            "description": (
                seo_result.meta_descriptions[0]
                if seo_result.meta_descriptions
                else content_analysis.summary
            ),
            "keywords": seo_result.keywords,
            "topics": content_analysis.key_topics,
        }

        # Prepare image data for publication
        image_data = {
            "total_processed": image_result.total_processed,
            "processing_time_ms": image_result.processing_time_ms,
            "processed_images": image_result.processed_images,
        }

        publication_manifest: PublicationManifest = await workflow.execute_activity(
            assemble_and_publish,
            args=[
                article_id,
                optimized_title,
                article.content,
                seo_metadata,
                image_data,
            ],
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info(
            f"Article published successfully: {publication_manifest.publication_url}"
        )

        return publication_manifest
