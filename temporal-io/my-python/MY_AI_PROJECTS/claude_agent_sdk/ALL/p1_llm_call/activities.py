"""Activities for Content Publishing Pipeline."""

import asyncio
import logging
import re
from io import BytesIO
from typing import Dict, List

from PIL import Image
from temporalio import activity

from shared.models import (
    ArticleInput,
    ContentAnalysis,
    ContentFormat,
    PublishedArticle,
    SEOOptimization,
    ValidationResult,
    ValidationStatus,
)

logger = logging.getLogger(__name__)


class ContentPublishingActivities:
    """Activities class for content publishing workflow."""

    @activity.defn
    async def validate_article_input(self, article: ArticleInput) -> ValidationResult:
        """
        Activity 1: Deterministic validation of article input.

        Validates:
        - Format (markdown/HTML)
        - Word count (min 100, max 10000)
        - Required metadata fields
        """
        logger.info(f"Validating article: {article.title}")

        errors: List[str] = []

        # Validate format
        if article.format not in [ContentFormat.MARKDOWN, ContentFormat.HTML]:
            errors.append(f"Invalid format: {article.format}")

        # Count words (simple whitespace split)
        word_count = len(article.content.split())

        if word_count < 100:
            errors.append(f"Word count too low: {word_count} (minimum 100)")
        elif word_count > 10000:
            errors.append(f"Word count too high: {word_count} (maximum 10000)")

        # Check required metadata fields
        required_fields = ["category", "tags"]
        for field in required_fields:
            if field not in article.metadata:
                errors.append(f"Missing required metadata field: {field}")

        # Check if author is provided
        if not article.author or len(article.author) < 2:
            errors.append("Author name must be at least 2 characters")

        status = ValidationStatus.VALID if not errors else ValidationStatus.INVALID

        result = ValidationResult(status=status, errors=errors, word_count=word_count)

        logger.info(f"Validation result: {status}, errors: {len(errors)}")
        return result

    @activity.defn
    async def analyze_content_with_llm(self, article: ArticleInput) -> ContentAnalysis:
        """
        Activity 2: LLM-powered content analysis.

        Uses Claude to:
        - Analyze tone and readability
        - Extract key topics
        - Generate summary
        - Identify sensitive topics
        """
        # Import SDK wrapper only when activity executes (not in workflow sandbox)
        from shared.sdk_wrapper import simple_query

        logger.info(f"Analyzing content with LLM: {article.title}")

        system_prompt = """You are an expert content analyst. Analyze the provided article and return:
1. Tone (e.g., formal, casual, technical, persuasive)
2. Readability score (0.0 to 1.0, where 1.0 is very readable)
3. Key topics (3-5 main topics)
4. A concise summary (2-3 sentences)
5. Any sensitive topics that might require careful handling

Return your analysis in this exact JSON format:
{
  "tone": "...",
  "readability_score": 0.85,
  "key_topics": ["topic1", "topic2", "topic3"],
  "summary": "...",
  "sensitive_topics": ["topic1", "topic2"]
}"""

        user_prompt = f"""Article Title: {article.title}

Article Content:
{article.content[:3000]}

Please analyze this article."""

        # Use SDK simple_query for stateless LLM call
        response_text = await simple_query(
            prompt=user_prompt,
            system_prompt=system_prompt
        )

        # Parse JSON response
        import json

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            json_str = json_match.group(0) if json_match else response_text

        try:
            analysis_data = json.loads(json_str)
            analysis = ContentAnalysis(**analysis_data)
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            # Fallback to default values
            analysis = ContentAnalysis(
                tone="neutral",
                readability_score=0.5,
                key_topics=["general"],
                summary="Content analysis unavailable",
                sensitive_topics=[],
            )

        logger.info(f"Content analysis complete: tone={analysis.tone}")
        return analysis

    @activity.defn
    async def optimize_for_seo(self, article: ArticleInput, analysis: ContentAnalysis) -> SEOOptimization:
        """
        Activity 3: LLM-powered SEO optimization.

        Generates:
        - SEO-friendly title alternatives
        - Meta descriptions
        - Relevant keywords
        - Internal linking suggestions
        """
        # Import SDK wrapper only when activity executes (not in workflow sandbox)
        from shared.sdk_wrapper import simple_query

        logger.info(f"Optimizing SEO for: {article.title}")

        system_prompt = """You are an SEO expert. Based on the article and its analysis, generate SEO optimizations.

Return your recommendations in this exact JSON format:
{
  "title_alternatives": ["title1", "title2", "title3"],
  "meta_description": "...",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "internal_linking_suggestions": ["related-article-1", "related-article-2"]
}"""

        user_prompt = f"""Article Title: {article.title}

Key Topics: {', '.join(analysis.key_topics)}
Tone: {analysis.tone}
Summary: {analysis.summary}

Article Content (excerpt):
{article.content[:2000]}

Please generate SEO optimization recommendations."""

        # Use SDK simple_query for stateless LLM call
        response_text = await simple_query(
            prompt=user_prompt,
            system_prompt=system_prompt
        )

        # Parse JSON response
        import json

        json_match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            json_str = json_match.group(0) if json_match else response_text

        try:
            seo_data = json.loads(json_str)
            seo = SEOOptimization(**seo_data)
        except Exception as e:
            logger.error(f"Failed to parse SEO response: {e}")
            seo = SEOOptimization(
                title_alternatives=[article.title],
                meta_description=analysis.summary[:160],
                keywords=analysis.key_topics[:5],
                internal_linking_suggestions=[],
            )

        logger.info(f"SEO optimization complete: {len(seo.keywords)} keywords generated")
        return seo

    @activity.defn
    async def process_images(self, article: ArticleInput) -> Dict[str, List[str]]:
        """
        Activity 4: Deterministic image processing.

        This is a simplified version that simulates:
        - Image resizing
        - Format conversion to WebP
        - Generating responsive variants
        - Updating image references
        """
        logger.info(f"Processing images for: {article.title}")

        # Extract image URLs from content (simple regex)
        img_pattern = r'!\[.*?\]\((.*?)\)|<img.*?src=["\'](.*?)["\']'
        matches = re.findall(img_pattern, article.content)

        # Flatten the tuple results
        image_urls = [url for match in matches for url in match if url]

        logger.info(f"Found {len(image_urls)} images to process")

        processed_images = {
            "original": image_urls,
            "resized": [f"{url}.resized" for url in image_urls],
            "webp": [f"{url}.webp" for url in image_urls],
            "responsive": [f"{url}.responsive" for url in image_urls],
        }

        # Simulate processing time
        await asyncio.sleep(0.5)

        logger.info(f"Image processing complete: {len(image_urls)} images processed")
        return processed_images

    @activity.defn
    async def assemble_and_publish(
        self,
        article: ArticleInput,
        analysis: ContentAnalysis,
        seo: SEOOptimization,
        processed_images: Dict[str, List[str]],
    ) -> PublishedArticle:
        """
        Activity 5: Deterministic final assembly and publication.

        Combines all optimized components and simulates publishing to CMS.
        """
        logger.info(f"Assembling and publishing: {article.title}")

        # Generate article ID
        import hashlib
        from datetime import datetime

        article_id = hashlib.md5(f"{article.title}{datetime.now()}".encode()).hexdigest()[:12]

        # Create publication manifest
        publication_metadata = {
            "original_title": article.title,
            "optimized_title": seo.title_alternatives[0] if seo.title_alternatives else article.title,
            "meta_description": seo.meta_description,
            "keywords": seo.keywords,
            "author": article.author,
            "category": article.metadata.get("category", "uncategorized"),
            "tags": article.metadata.get("tags", []),
            "tone": analysis.tone,
            "readability_score": analysis.readability_score,
            "word_count": len(article.content.split()),
            "images_processed": len(processed_images.get("original", [])),
            "key_topics": analysis.key_topics,
        }

        # Simulate publishing delay
        await asyncio.sleep(0.3)

        published = PublishedArticle(
            article_id=article_id,
            publication_url=f"https://example.com/articles/{article_id}",
            published_at=datetime.now(),
            metadata=publication_metadata,
        )

        logger.info(f"Article published: {published.publication_url}")
        return published
