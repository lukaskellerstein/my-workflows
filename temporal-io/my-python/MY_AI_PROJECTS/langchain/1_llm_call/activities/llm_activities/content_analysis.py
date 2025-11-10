"""LLM-powered content analysis activities."""

from dataclasses import dataclass
from temporalio import activity
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field


class ContentAnalysisSchema(BaseModel):
    """Schema for content analysis response."""

    tone: str = Field(description="Tone of the content: professional, casual, technical, educational, or conversational")
    readability_score: str = Field(description="Readability: easy, medium, or difficult")
    key_topics: list[str] = Field(description="List of key topics covered")
    themes: list[str] = Field(description="Main themes of the content")
    summary: str = Field(description="Brief 2-3 sentence summary")
    sensitive_topics: list[str] = Field(description="Any sensitive topics identified")
    recommendations: list[str] = Field(description="Recommendations for improvement")


@dataclass
class ContentAnalysisResult:
    """Result of content analysis."""

    tone: str
    readability_score: str
    key_topics: list[str]
    themes: list[str]
    summary: str
    sensitive_topics: list[str]
    recommendations: list[str]


@activity.defn
async def analyze_content(content: str, title: str) -> ContentAnalysisResult:
    """
    Analyze article content using Claude LLM.

    This activity uses an LLM to analyze content tone, readability,
    topics, and identify any sensitive subjects.

    Args:
        content: Article content to analyze
        title: Article title

    Returns:
        ContentAnalysisResult with analysis details
    """
    activity.logger.info(f"Analyzing content for: {title}")

    # Create LLM with structured output
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.3)
    llm_with_structure = llm.with_structured_output(ContentAnalysisSchema)

    # Create conversation
    conversation = [
        {
            "role": "system",
            "content": "You are a professional content analyst. Analyze the provided article thoroughly."
        },
        {
            "role": "user",
            "content": f"Title: {title}\n\nContent:\n{content[:5000]}\n\nAnalyze this article's tone, readability, topics, themes, and any sensitive subjects."
        }
    ]

    # Execute
    try:
        result = await llm_with_structure.ainvoke(conversation)

        analysis = ContentAnalysisResult(
            tone=result.tone,
            readability_score=result.readability_score,
            key_topics=result.key_topics,
            themes=result.themes,
            summary=result.summary,
            sensitive_topics=result.sensitive_topics,
            recommendations=result.recommendations,
        )

        activity.logger.info(
            f"Content analysis completed. Tone: {analysis.tone}, Topics: {len(analysis.key_topics)}"
        )

        return analysis

    except Exception as e:
        activity.logger.error(f"Error during content analysis: {e}")
        # Return default analysis on error
        return ContentAnalysisResult(
            tone="unknown",
            readability_score="medium",
            key_topics=[],
            themes=[],
            summary="Analysis failed",
            sensitive_topics=[],
            recommendations=["Manual review recommended"],
        )
