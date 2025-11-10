from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

# ============================================================================
# Project 2: Research Assistant Models
# ============================================================================


class SourceType(str, Enum):
    """Type of research source."""

    WEB = "web"
    ACADEMIC = "academic"


class ResearchFact(BaseModel):
    """Individual fact extracted from source."""

    fact: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_text: str


class ResearchSource(BaseModel):
    """Research source document."""

    id: str = Field(default_factory=lambda: "")
    run_id: str
    type: SourceType
    title: str
    url: Optional[str] = None
    doi: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    date_published: Optional[datetime] = None
    date_collected: Optional[datetime] = None
    credibility_score: float = Field(ge=0.0, le=1.0, default=0.5)

    # Content fields - the actual text
    content: Optional[str] = None  # Full article text or paper content
    abstract: Optional[str] = None  # Abstract for academic papers
    summary: Optional[str] = None  # AI-generated summary if full content unavailable
    raw_content: Optional[str] = None  # Raw HTML or unprocessed content

    # Extracted information
    key_facts: List[ResearchFact] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
