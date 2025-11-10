"""Data models for research assistant pipeline."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ResearchQuery:
    """Input model for research query."""

    query: str
    max_sources: int = 20
    include_academic: bool = True
    include_web: bool = True
    generate_audio: bool = False


@dataclass
class SourceDocument:
    """A single research source."""

    source_id: str
    type: str  # "web" or "academic"
    title: str
    url: Optional[str] = None
    doi: Optional[str] = None
    authors: list[str] = field(default_factory=list)
    date_published: Optional[str] = None
    date_collected: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    credibility_score: float = 0.5
    key_facts: list[dict] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    abstract: Optional[str] = None
    content_summary: Optional[str] = None


@dataclass
class KnowledgeGraphNode:
    """A node in the knowledge graph."""

    node_id: str
    type: str  # "concept", "person", "organization", "event"
    name: str
    description: str
    relationships: list[dict] = field(default_factory=list)
    first_seen: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ResearchContext:
    """Context retrieved from MongoDB."""

    related_sessions: list[dict] = field(default_factory=list)
    existing_sources: int = 0
    known_topics: list[str] = field(default_factory=list)
    knowledge_gaps: list[str] = field(default_factory=list)


@dataclass
class DataEnrichment:
    """Results of data enrichment."""

    total_sources: int
    deduplicated_sources: int
    cross_references: int
    average_credibility: float


@dataclass
class ResearchSynthesis:
    """Synthesized research report."""

    title: str
    executive_summary: str
    main_findings: list[dict]  # {"finding": str, "sources": [ids], "confidence": float}
    conflicting_viewpoints: list[dict]  # {"topic": str, "viewpoints": [{}]}
    knowledge_gaps: list[str]
    confidence_level: float
    sources_count: int
    synthesis_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class AudioReport:
    """Audio report metadata."""

    audio_id: str
    audio_url: str
    duration_seconds: float
    chapters: list[dict]  # {"title": str, "timestamp": float}
    transcript_url: Optional[str] = None


@dataclass
class ResearchSession:
    """Complete research session result."""

    session_id: str
    query: str
    context: ResearchContext
    web_sources: list[SourceDocument]
    academic_sources: list[SourceDocument]
    enrichment: DataEnrichment
    knowledge_graph_nodes: int
    synthesis: ResearchSynthesis
    audio_report: Optional[AudioReport] = None
    total_tokens_used: int = 0
    duration_seconds: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
