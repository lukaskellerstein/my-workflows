"""LLM-powered activities for content analysis and optimization."""

import asyncio
from pydantic import BaseModel
from temporalio import activity
from agents import Agent, Runner

from models import ArticleInput, ContentAnalysis, SEOOptimization


# Pydantic models for structured outputs
class ContentAnalysisOutput(BaseModel):
    """Structured output for content analysis."""

    tone: str
    readability_score: float
    topics: list[str]
    summary: str
    sensitive_topics: list[str] = []


@activity.defn
async def analyze_content(article: ArticleInput, word_count: int) -> ContentAnalysis:
    """
    LLM Activity: Analyze content tone, readability, and topics.

    Uses OpenAI Agent with structured output_type for reliable results.
    """
    activity.logger.info(f"Analyzing content: {article.title} ({word_count} words)")

    # Send heartbeat to show activity is alive
    activity.heartbeat("Starting content analysis")

    agent = Agent(
        name="Content Analyzer",
        model="gpt-5-mini",  # Use correct model name
        instructions="""You are a professional content analyst. Analyze the given article and provide:
        1. Overall tone (professional, casual, technical, persuasive, etc.)
        2. Readability score (0-100, where 100 is very easy to read)
        3. Main topics and themes (list of 3-7 topics)
        4. A brief summary (2-3 sentences)
        5. Any potentially sensitive topics (politics, religion, controversial subjects)
        """,
        output_type=ContentAnalysisOutput,
    )

    prompt = f"""Article Title: {article.title}
Author: {article.author}
Word Count: {word_count}
Tags: {', '.join(article.tags) if article.tags else 'None'}

Content:
{article.content[:3000]}{"..." if len(article.content) > 3000 else ""}
"""

    activity.heartbeat("Calling LLM")

    try:
        result = await Runner.run(agent, input=prompt)

        activity.heartbeat("Processing LLM response")

        # Extract structured output
        output: ContentAnalysisOutput = result.final_output

        analysis = ContentAnalysis(
            tone=output.tone,
            readability_score=output.readability_score,
            topics=output.topics,
            summary=output.summary,
            sensitive_topics=output.sensitive_topics,
        )

        activity.logger.info(
            f"Analysis complete - Tone: {analysis.tone}, "
            f"Readability: {analysis.readability_score}, "
            f"Topics: {len(analysis.topics)}"
        )

        return analysis

    except asyncio.CancelledError:
        activity.logger.warning("Activity was cancelled")
        raise
    except Exception as e:
        activity.logger.warning(f"Failed to process LLM response: {e}")
        # Return default analysis
        return ContentAnalysis(
            tone="neutral",
            readability_score=50.0,
            topics=["general"],
            summary="Content analysis unavailable",
            sensitive_topics=[],
        )


class SEOOptimizationOutput(BaseModel):
    """Structured output for SEO optimization."""

    title_alternatives: list[str]
    meta_description: str
    keywords: list[str]
    internal_links: list[str]


@activity.defn
async def optimize_seo(
    article: ArticleInput,
    analysis: ContentAnalysis,
) -> SEOOptimization:
    """
    LLM Activity: Generate SEO-friendly metadata and recommendations.

    Uses OpenAI Agent with structured output_type for reliable results.
    """
    activity.logger.info(f"Optimizing SEO for: {article.title}")

    # Send heartbeat to show activity is alive
    activity.heartbeat("Starting SEO optimization")

    agent = Agent(
        name="SEO Specialist",
        model="gpt-5-mini",  # Use correct model name
        instructions="""You are an expert SEO specialist. Based on the article content and analysis, provide:
        1. 3-5 alternative SEO-friendly titles (catchy, keyword-rich, under 60 characters)
        2. A compelling meta description (150-160 characters)
        3. 5-10 relevant keywords for SEO
        4. Suggestions for internal linking opportunities (3-5 related topics to link)
        """,
        output_type=SEOOptimizationOutput,
    )

    prompt = f"""Current Title: {article.title}
Author: {article.author}
Content Topics: {', '.join(analysis.topics)}
Content Tone: {analysis.tone}
Content Summary: {analysis.summary}

Original Content (first 2000 chars):
{article.content[:2000]}{"..." if len(article.content) > 2000 else ""}
"""

    activity.heartbeat("Calling LLM")

    try:
        result = await Runner.run(agent, input=prompt)

        activity.heartbeat("Processing LLM response")

        # Extract structured output
        output: SEOOptimizationOutput = result.final_output

        seo = SEOOptimization(
            title_alternatives=output.title_alternatives,
            meta_description=output.meta_description[:160],
            keywords=output.keywords,
            internal_links=output.internal_links,
        )

        activity.logger.info(
            f"SEO optimization complete - "
            f"{len(seo.title_alternatives)} title alternatives, "
            f"{len(seo.keywords)} keywords"
        )

        return seo

    except asyncio.CancelledError:
        activity.logger.warning("Activity was cancelled")
        raise
    except Exception as e:
        activity.logger.warning(f"Failed to process LLM response: {e}")
        # Return default SEO
        return SEOOptimization(
            title_alternatives=[article.title],
            meta_description=analysis.summary[:160] if analysis.summary else "",
            keywords=analysis.topics[:5] if analysis.topics else [],
            internal_links=[],
        )
