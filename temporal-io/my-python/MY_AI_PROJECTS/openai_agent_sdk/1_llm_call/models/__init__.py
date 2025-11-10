"""Data models for content publishing pipeline."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ArticleInput:
    """Input model for article submission."""

    content: str
    title: str
    author: str
    format: str = "markdown"  # markdown or html
    tags: list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class ValidationResult:
    """Result of content validation."""

    is_valid: bool
    errors: list[str]
    word_count: int
    metadata: dict


@dataclass
class ContentAnalysis:
    """LLM-generated content analysis."""

    tone: str
    readability_score: float
    topics: list[str]
    summary: str
    sensitive_topics: list[str]


@dataclass
class SEOOptimization:
    """LLM-generated SEO recommendations."""

    title_alternatives: list[str]
    meta_description: str
    keywords: list[str]
    internal_links: list[str]


@dataclass
class ImageMetadata:
    """Processed image information."""

    original_path: str
    optimized_paths: dict[str, str]  # format -> path
    dimensions: dict[str, tuple[int, int]]  # format -> (width, height)


@dataclass
class PublicationManifest:
    """Final publication package."""

    publication_id: str
    publication_url: str
    title: str
    content: str
    metadata: dict
    seo: SEOOptimization
    images: list[ImageMetadata]
    timestamp: str
