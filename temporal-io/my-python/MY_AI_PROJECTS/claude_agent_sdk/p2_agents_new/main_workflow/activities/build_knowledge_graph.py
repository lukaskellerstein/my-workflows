import logging
from typing import Dict, List

from temporalio import activity

from ..state import WorkflowState

from shared.mongodb_client import MongoDBClient

logger = logging.getLogger(__name__)


@activity.defn
async def build_knowledge_graph(state: WorkflowState) -> List[Dict]:
    """
    Activity 5: Build knowledge graph (AI Agent + MongoDB).

    Uses KnowledgeGraphAgent to:
    - Identify entities and relationships
    - Detect conflicting information
    - Store confidence scores
    """
    # Import agent only when activity executes (not in workflow sandbox)
    from agents import KnowledgeGraphAgent

    logger.info(f"Building knowledge graph for run_id: {state.run_id}")

    db = MongoDBClient()
    await db.connect()
    try:
        agent = KnowledgeGraphAgent()
        nodes = await agent.execute(state=state, db=db)

        nodes_dicts = [n.model_dump() for n in nodes]

        logger.info(f"Knowledge graph complete: {len(nodes)} nodes")
        return nodes_dicts
    finally:
        await db.disconnect()
