"""Activity implementations for content publishing pipeline."""

import re
from datetime import datetime
from typing import Optional
from temporalio import activity

from models import (
    ArticleInput,
    ValidationResult,
    ContentAnalysis,
    SEOOptimization,
    ImageMetadata,
    PublicationManifest,
)


@activity.defn
async def validate_article(article: ArticleInput) -> ValidationResult:
    """
    Deterministic activity: Validate article format and content.

    Checks:
    - Valid format (markdown/html)
    - Word count range (100-10000 words)
    - Required metadata fields
    """
    activity.logger.info(f"Validating article: {article.title}")

    errors = []

    # Validate format
    if article.format not in ["markdown", "html"]:
        errors.append(f"Invalid format: {article.format}. Must be 'markdown' or 'html'")

    # Count words
    text_content = re.sub(r'<[^>]+>', '', article.content)  # Strip HTML tags
    text_content = re.sub(r'[#*_\[\]`]', '', text_content)  # Strip markdown
    words = text_content.split()
    word_count = len(words)

    # Validate word count
    if word_count < 100:
        errors.append(f"Article too short: {word_count} words (minimum 100)")
    elif word_count > 10000:
        errors.append(f"Article too long: {word_count} words (maximum 10000)")

    # Validate required fields
    if not article.title or len(article.title.strip()) == 0:
        errors.append("Title is required")

    if not article.author or len(article.author.strip()) == 0:
        errors.append("Author is required")

    # Build metadata
    metadata = {
        "format": article.format,
        "author": article.author,
        "tags": article.tags,
        "validated_at": datetime.utcnow().isoformat(),
    }

    is_valid = len(errors) == 0

    activity.logger.info(
        f"Validation complete: {'PASSED' if is_valid else 'FAILED'} "
        f"({word_count} words, {len(errors)} errors)"
    )

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        word_count=word_count,
        metadata=metadata,
    )


@activity.defn
async def process_images(content: str) -> list[ImageMetadata]:
    """
    Deterministic activity: Process and optimize images.

    In a real implementation, this would:
    - Extract image references from content
    - Resize and optimize images
    - Generate responsive variants
    - Create WebP versions

    For demo purposes, this simulates the process.
    """
    activity.logger.info("Processing images in content")

    # Extract image references (simplified regex)
    image_pattern = r'!\[.*?\]\((.*?)\)|<img.*?src=["\']([^"\']*)["\']'
    matches = re.findall(image_pattern, content)

    images = []
    for match in matches:
        # match is a tuple from regex groups
        image_path = match[0] if match[0] else match[1]
        if not image_path:
            continue

        # Simulate image processing
        processed = ImageMetadata(
            original_path=image_path,
            optimized_paths={
                "original": image_path,
                "webp": image_path.rsplit('.', 1)[0] + '.webp' if '.' in image_path else image_path + '.webp',
                "thumbnail": image_path.rsplit('.', 1)[0] + '_thumb.jpg' if '.' in image_path else image_path + '_thumb.jpg',
            },
            dimensions={
                "original": (1200, 800),
                "thumbnail": (300, 200),
            }
        )
        images.append(processed)

    activity.logger.info(f"Processed {len(images)} images")
    return images


@activity.defn
async def assemble_publication(
    article: ArticleInput,
    validation: ValidationResult,
    analysis: ContentAnalysis,
    seo: SEOOptimization,
    images: list[ImageMetadata],
) -> PublicationManifest:
    """
    Deterministic activity: Create final publication package.

    Combines all processed data into a publication manifest.
    """
    activity.logger.info(f"Assembling publication for: {article.title}")

    # Generate publication ID
    timestamp = datetime.utcnow()
    pub_id = f"pub_{timestamp.strftime('%Y%m%d_%H%M%S')}_{article.title[:20].replace(' ', '_')}"

    # Create publication URL (simulated)
    pub_url = f"https://example.com/articles/{pub_id}"

    # Combine metadata
    full_metadata = {
        **validation.metadata,
        "word_count": validation.word_count,
        "tone": analysis.tone,
        "readability": analysis.readability_score,
        "topics": analysis.topics,
        "sensitive_topics": analysis.sensitive_topics,
        "keywords": seo.keywords,
        "published_at": timestamp.isoformat(),
    }

    manifest = PublicationManifest(
        publication_id=pub_id,
        publication_url=pub_url,
        title=article.title,
        content=article.content,
        metadata=full_metadata,
        seo=seo,
        images=images,
        timestamp=timestamp.isoformat(),
    )

    activity.logger.info(f"Publication assembled: {pub_url}")
    return manifest
