"""Deterministic publication activities."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from temporalio import activity


@dataclass
class PublicationManifest:
    """Final publication manifest."""

    article_id: str
    title: str
    content: str
    metadata: dict[str, Any]
    publication_url: str
    published_at: str
    status: str


@activity.defn
async def assemble_and_publish(
    article_id: str,
    title: str,
    optimized_content: str,
    seo_metadata: dict,
    image_data: dict,
) -> PublicationManifest:
    """
    Assemble final article and publish to CMS.

    This is a deterministic activity that combines all processed data
    and "publishes" the article (simulated).

    Args:
        article_id: Unique article identifier
        title: Article title
        optimized_content: Content with SEO optimizations
        seo_metadata: SEO metadata (title, description, keywords)
        image_data: Processed image data

    Returns:
        PublicationManifest with publication details
    """
    activity.logger.info(f"Publishing article: {article_id}")

    # Simulate storing in CMS
    publication_url = f"https://example.com/articles/{article_id}"

    # Create complete metadata
    metadata = {
        "seo": seo_metadata,
        "images": {
            "count": image_data.get("total_processed", 0),
            "processing_time_ms": image_data.get("processing_time_ms", 0),
        },
        "word_count": len(optimized_content.split()),
        "published_by": "content_publishing_workflow",
    }

    manifest = PublicationManifest(
        article_id=article_id,
        title=title,
        content=optimized_content,
        metadata=metadata,
        publication_url=publication_url,
        published_at=datetime.utcnow().isoformat(),
        status="published",
    )

    activity.logger.info(f"Article published successfully: {publication_url}")

    return manifest
