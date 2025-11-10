"""LLM-powered SEO optimization activities."""

from dataclasses import dataclass
from temporalio import activity
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field


class LinkingSuggestion(BaseModel):
    """Internal linking suggestion."""
    anchor_text: str = Field(description="Suggested anchor text for the link")
    suggested_topic: str = Field(description="Related topic to link to")


class SEOSchema(BaseModel):
    """Schema for SEO optimization response."""

    title_alternatives: list[str] = Field(description="3 SEO-friendly title alternatives under 60 characters")
    meta_descriptions: list[str] = Field(description="3 meta descriptions between 150-160 characters")
    keywords: list[str] = Field(description="List of relevant keywords")
    internal_linking_suggestions: list[LinkingSuggestion] = Field(description="Internal linking suggestions")
    content_recommendations: list[str] = Field(description="SEO improvement recommendations")


@dataclass
class SEOResult:
    """Result of SEO optimization."""

    title_alternatives: list[str]
    meta_descriptions: list[str]
    keywords: list[str]
    internal_linking_suggestions: list[dict[str, str]]
    content_recommendations: list[str]


@activity.defn
async def optimize_seo(
    content: str, title: str, key_topics: list[str]
) -> SEOResult:
    """
    Generate SEO optimizations using Claude LLM.

    This activity uses an LLM to create SEO-friendly titles,
    meta descriptions, keywords, and linking suggestions.

    Args:
        content: Article content
        title: Original article title
        key_topics: Key topics from content analysis

    Returns:
        SEOResult with optimization suggestions
    """
    activity.logger.info(f"Optimizing SEO for: {title}")

    # Create LLM with structured output
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.7)
    llm_with_structure = llm.with_structured_output(SEOSchema)

    # Create conversation
    topics_str = ", ".join(key_topics[:5]) if key_topics else "general"
    conversation = [
        {
            "role": "system",
            "content": "You are an SEO expert. Create SEO optimizations for the provided article. "
                       "Meta descriptions must be 150-160 characters. Titles must be under 60 characters."
        },
        {
            "role": "user",
            "content": f"Original Title: {title}\n\nKey Topics: {topics_str}\n\nContent Preview:\n{content[:3000]}\n\n"
                       "Generate SEO-optimized titles, meta descriptions, keywords, and recommendations."
        }
    ]

    # Execute
    try:
        result = await llm_with_structure.ainvoke(conversation)

        seo_result = SEOResult(
            title_alternatives=result.title_alternatives[:3],
            meta_descriptions=result.meta_descriptions[:3],
            keywords=result.keywords[:10],
            internal_linking_suggestions=[
                {"anchor_text": s.anchor_text, "suggested_topic": s.suggested_topic}
                for s in result.internal_linking_suggestions[:5]
            ],
            content_recommendations=result.content_recommendations[:5],
        )

        activity.logger.info(
            f"SEO optimization completed. Generated {len(seo_result.title_alternatives)} title alternatives"
        )

        return seo_result

    except Exception as e:
        activity.logger.error(f"Error during SEO optimization: {e}")
        # Return default SEO data on error
        return SEOResult(
            title_alternatives=[title],
            meta_descriptions=[f"Read about {title}"],
            keywords=key_topics[:5] if key_topics else [],
            internal_linking_suggestions=[],
            content_recommendations=["Manual SEO review recommended"],
        )
