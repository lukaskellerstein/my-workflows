from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================================
class NodeType(str, Enum):
    """Knowledge graph node types."""

    CONCEPT = "concept"
    PERSON = "person"
    ORGANIZATION = "organization"
    EVENT = "event"


class RelationType(str, Enum):
    """Knowledge graph relationship types.

    Based on common knowledge graph ontologies and semantic web standards.
    """

    # Generic relationships
    RELATED_TO = "related_to"
    IS_A = "is_a"  # Type/subclass relationship
    PART_OF = "part_of"  # Compositional relationship
    CONTAINS = "contains"  # Inverse of part_of

    # Logical relationships
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    IMPLIES = "implies"
    EQUIVALENT_TO = "equivalent_to"
    COMPLEMENTS = "complements"  # Mutually reinforcing relationship

    # Causal relationships (from Dimensions Knowledge Graph)
    CAUSES = "causes"
    CAUSED_BY = "caused_by"  # Inverse of causes
    INCREASES = "increases"
    DECREASED_BY = "decreased_by"  # Inverse of decreases
    DECREASES = "decreases"
    INFLUENCES = "influences"
    INFLUENCED_BY = "influenced_by"  # Inverse of influences
    MODULATES = "modulates"
    PREVENTS = "prevents"
    ENABLES = "enables"
    AFFECTS = "affects"  # General effect relationship
    REDUCED = "reduced"  # Past tense causal

    # Measurement and evaluation relationships
    MEASURED_BY = "measured_by"
    MEASURED = "measured"  # Past tense
    EVALUATED_ON = "evaluated_on"
    PUBLISHED = "published"  # Attribution for publication

    # Correlation relationships
    INVERSELY_RELATED = "inversely_related"  # Negative correlation

    # Usage relationships
    USES = "uses"
    USED_BY = "used_by"  # Inverse of uses
    REQUIRES = "requires"  # Dependency relationship

    # Temporal relationships
    PRECEDED_BY = "preceded_by"
    FOLLOWED_BY = "followed_by"
    CONCURRENT_WITH = "concurrent_with"

    # Attribution relationships
    DEVELOPED_BY = "developed_by"
    CREATED_BY = "created_by"
    DISCOVERED_BY = "discovered_by"

    # Domain relationships
    APPLIES_TO = "applies_to"
    USED_IN = "used_in"
    BASED_ON = "based_on"
    DERIVED_FROM = "derived_from"


class Relationship(BaseModel):
    """Knowledge graph relationship."""

    target_id: str
    relationship_type: RelationType
    confidence: float = Field(ge=0.0, le=1.0)
    source_ids: List[str] = Field(default_factory=list)


class KnowledgeGraphNode(BaseModel):
    """Knowledge graph node."""

    id: str
    run_id: str
    type: NodeType
    name: str
    description: str
    relationships: List[Relationship] = Field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_updated: Optional[datetime] = None
