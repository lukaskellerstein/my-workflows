from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
class ResearchSynthesis(BaseModel):
    """Synthesized research report with dual outputs."""

    run_id: str
    main_findings: List[str]
    conflicting_viewpoints: List[Dict[str, Any]]
    knowledge_gaps: List[str]
    confidence_levels: Dict[str, float]
    sources_used: List[str]

    # Dual outputs for different consumption modes
    text_report: str = Field(default="", description="Formatted text for reading (bullets, numbers, sections)")
    audio_script: str = Field(default="", description="Natural narrative for text-to-speech conversion")
