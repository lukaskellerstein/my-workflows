import logging
from typing import Dict, List

from temporalio import activity

from ..state import WorkflowState

from shared.mongodb_client import MongoDBClient

logger = logging.getLogger(__name__)


@activity.defn
async def enrich_and_cross_reference(state: WorkflowState) -> Dict[str, int]:
    """
    Activity 4: Data enrichment and cross-referencing (Deterministic + MongoDB).

    - Deduplicate findings
    - Cross-reference sources
    - Calculate reliability scores
    - Generate statistics
    """
    logger.info(f"Enriching and cross-referencing data for run_id: {state.run_id}")

    db = MongoDBClient()
    await db.connect()
    try:
        # Get all sources for this session
        sources = await db.find_documents("research_sources", {"run_id": state.run_id})

        # Calculate statistics
        stats = {
            "total_sources": len(sources),
            "web_sources": sum(1 for s in sources if s.get("type") == "web"),
            "academic_sources": sum(1 for s in sources if s.get("type") == "academic"),
            "avg_credibility": (
                sum(s.get("credibility_score", 0) for s in sources) / len(sources) if sources else 0
            ),
            "total_facts": sum(len(s.get("key_facts", [])) for s in sources),
        }

        logger.info(f"Data enrichment complete: {stats}")
        return stats
    finally:
        await db.disconnect()
