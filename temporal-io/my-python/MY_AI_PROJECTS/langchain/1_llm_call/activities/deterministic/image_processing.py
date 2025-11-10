"""Deterministic image processing activities."""

from dataclasses import dataclass
from typing import Optional
from temporalio import activity


@dataclass
class ImageProcessingResult:
    """Result of image processing."""

    original_images: list[str]
    processed_images: dict[str, list[str]]  # image_name -> [variants]
    total_processed: int
    processing_time_ms: float


@activity.defn
async def process_images(content: str, article_id: str) -> ImageProcessingResult:
    """
    Process and optimize images in the article content.

    This is a deterministic activity that simulates image processing.
    In a real implementation, this would:
    - Extract image references from content
    - Resize and optimize images
    - Generate responsive variants
    - Create WebP versions
    - Update image references

    Args:
        content: Article content
        article_id: Unique article identifier

    Returns:
        ImageProcessingResult with processing details
    """
    activity.logger.info(f"Processing images for article: {article_id}")

    # Simulate extracting image references (simplified)
    # In reality, would parse markdown/html for image tags
    import re
    import time

    start_time = time.time()

    # Simple regex to find markdown images: ![alt](url)
    markdown_images = re.findall(r"!\[.*?\]\((.*?)\)", content)

    # Simple regex to find html images: <img src="url"
    html_images = re.findall(r'<img[^>]+src="([^"]+)"', content)

    all_images = list(set(markdown_images + html_images))

    processed_images = {}

    for img in all_images:
        # Simulate creating variants
        variants = [
            f"{img}.thumb.jpg",  # Thumbnail
            f"{img}.medium.jpg",  # Medium size
            f"{img}.large.jpg",  # Large size
            f"{img}.webp",  # WebP version
        ]
        processed_images[img] = variants

    processing_time = (time.time() - start_time) * 1000  # Convert to ms

    activity.logger.info(
        f"Processed {len(all_images)} images in {processing_time:.2f}ms"
    )

    return ImageProcessingResult(
        original_images=all_images,
        processed_images=processed_images,
        total_processed=len(all_images),
        processing_time_ms=processing_time,
    )
