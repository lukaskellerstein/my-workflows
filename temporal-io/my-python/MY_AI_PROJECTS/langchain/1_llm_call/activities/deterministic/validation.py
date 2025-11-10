"""Deterministic validation activities for content publishing."""

from dataclasses import dataclass
from typing import Optional
from temporalio import activity


@dataclass
class ArticleInput:
    """Input data for article processing."""

    content: str
    title: str
    format: str  # 'markdown' or 'html'
    author: Optional[str] = None
    tags: Optional[list[str]] = None


@dataclass
class ValidationResult:
    """Result of article validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    metadata: dict


@activity.defn
async def validate_article(article: ArticleInput) -> ValidationResult:
    """
    Validate article format and content requirements.

    Args:
        article: Article input data

    Returns:
        ValidationResult with validation status and any errors
    """
    activity.logger.info(f"Validating article: {article.title}")

    errors = []
    warnings = []

    # Check format
    if article.format not in ["markdown", "html"]:
        errors.append(f"Invalid format: {article.format}. Must be 'markdown' or 'html'")

    # Check word count
    word_count = len(article.content.split())
    if word_count < 100:
        errors.append(f"Content too short: {word_count} words (minimum 100)")
    elif word_count > 10000:
        errors.append(f"Content too long: {word_count} words (maximum 10000)")

    # Check title
    if not article.title or len(article.title) < 5:
        errors.append("Title is required and must be at least 5 characters")
    elif len(article.title) > 200:
        errors.append(f"Title too long: {len(article.title)} characters (maximum 200)")

    # Check for empty content
    if not article.content or article.content.strip() == "":
        errors.append("Content cannot be empty")

    # Warnings for missing optional fields
    if not article.author:
        warnings.append("Author not specified")

    if not article.tags or len(article.tags) == 0:
        warnings.append("No tags provided")

    metadata = {
        "word_count": word_count,
        "title_length": len(article.title),
        "format": article.format,
        "has_author": bool(article.author),
        "tag_count": len(article.tags) if article.tags else 0,
    }

    is_valid = len(errors) == 0

    activity.logger.info(
        f"Validation {'passed' if is_valid else 'failed'} for: {article.title}"
    )

    return ValidationResult(
        is_valid=is_valid, errors=errors, warnings=warnings, metadata=metadata
    )
