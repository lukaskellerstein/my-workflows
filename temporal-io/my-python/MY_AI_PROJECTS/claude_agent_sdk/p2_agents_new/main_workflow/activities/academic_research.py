import logging
from typing import Dict, List

from temporalio import activity

from ..state import WorkflowState

from shared.mongodb_client import MongoDBClient

logger = logging.getLogger(__name__)


@activity.defn
async def academic_research_activity(state: WorkflowState) -> List[Dict]:
    """
    Activity 3: Academic research using Academia MCP (AI Agent + MongoDB).

    Uses AcademicResearchAgent to:
    - Search for peer-reviewed papers
    - Extract key findings and methodologies
    - Build citation network
    """
    # Import agent only when activity executes (not in workflow sandbox)
    from agents import AcademicResearchAgent

    logger.info(f"Starting academic research for run_id: {state.run_id}")

    db = MongoDBClient()
    await db.connect()
    try:
        agent = AcademicResearchAgent()
        sources = await agent.execute(state=state, db=db, max_papers=5)

        sources_dicts = [s.model_dump() for s in sources]

        logger.info(f"Academic research complete: {len(sources)} papers")
        return sources_dicts
    finally:
        await db.disconnect()
