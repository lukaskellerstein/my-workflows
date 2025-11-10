"""Deterministic query parsing and context retrieval activities."""

from dataclasses import dataclass
from typing import Optional
from temporalio import activity


@dataclass
class QueryContext:
    """Parsed query context."""

    original_query: str
    key_terms: list[str]
    query_type: str  # 'academic', 'web', 'general'
    time_range: Optional[str]
    related_past_sessions: list[str]
    knowledge_gaps: list[str]


@activity.defn
async def parse_research_query(
    query: str, past_sessions: list[dict]
) -> QueryContext:
    """
    Parse research query and identify search parameters.

    Args:
        query: User's research question
        past_sessions: Related past research sessions

    Returns:
        QueryContext with parsed information
    """
    activity.logger.info(f"Parsing research query: {query[:50]}...")

    # Simple keyword extraction (in production, use NLP)
    import re

    words = re.findall(r"\b\w+\b", query.lower())
    stopwords = {
        "what",
        "is",
        "the",
        "how",
        "why",
        "when",
        "where",
        "a",
        "an",
        "and",
        "or",
    }
    key_terms = [w for w in words if w not in stopwords and len(w) > 3][:10]

    # Determine query type
    query_type = "general"
    if any(word in query.lower() for word in ["research", "study", "paper"]):
        query_type = "academic"
    elif any(word in query.lower() for word in ["news", "current", "latest"]):
        query_type = "web"

    # Extract time range if mentioned
    time_range = None
    if "recent" in query.lower() or "latest" in query.lower():
        time_range = "1 month"
    elif "this year" in query.lower():
        time_range = "1 year"

    # Identify related sessions
    related_sessions = [s["_id"] for s in past_sessions[:3]]

    # Identify knowledge gaps (simplified)
    knowledge_gaps = [f"Need information about: {term}" for term in key_terms[:3]]

    activity.logger.info(f"Parsed query type: {query_type}, key terms: {key_terms[:5]}")

    return QueryContext(
        original_query=query,
        key_terms=key_terms,
        query_type=query_type,
        time_range=time_range,
        related_past_sessions=related_sessions,
        knowledge_gaps=knowledge_gaps,
    )
