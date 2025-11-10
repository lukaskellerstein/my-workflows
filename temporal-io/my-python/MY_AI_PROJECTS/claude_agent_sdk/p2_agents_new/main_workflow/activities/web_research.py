import logging
from typing import Dict, List

from temporalio import activity

from ..state import WorkflowState

from shared.mongodb_client import MongoDBClient

logger = logging.getLogger(__name__)


@activity.defn
async def web_research_activity(state: WorkflowState) -> List[Dict]:
    """
    Activity 2: Web research using Tavily (AI Agent + MongoDB).

    Uses WebResearchAgent to:
    - Search for relevant articles
    - Extract and store findings
    - Tag content with topics
    """
    # Import agent only when activity executes (not in workflow sandbox)
    from agents import WebResearchAgent

    logger.info(f"Starting web research for run_id: {state.run_id}")

    db = MongoDBClient()
    await db.connect()
    try:
        agent = WebResearchAgent()
        sources = await agent.execute(state=state, db=db, max_sources=5)

        # Convert to dicts for serialization
        sources_dicts = [s.model_dump() for s in sources]

        logger.info(f"Web research complete: {len(sources)} sources")

        return sources_dicts
    finally:
        await db.disconnect()
