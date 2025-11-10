"""Shared data models across all projects."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

# ============================================================================


class WorkflowState(BaseModel):
    """State object passed between workflow activities."""

    query: str
    run_id: str
    web_sources: List[Dict] = Field(default_factory=list)
    academic_sources: List[Dict] = Field(default_factory=list)
    knowledge_graph: List[Dict] = Field(default_factory=list)
    synthesis: Optional[Dict] = None
