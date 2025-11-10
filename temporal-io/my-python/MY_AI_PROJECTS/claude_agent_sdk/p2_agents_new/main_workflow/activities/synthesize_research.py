import logging
from typing import Dict, List

from temporalio import activity

from ..state import WorkflowState

from shared.mongodb_client import MongoDBClient

logger = logging.getLogger(__name__)


@activity.defn
async def synthesize_research(state: WorkflowState) -> Dict:
    """
    Activity 6: Synthesize research findings (AI Agent + Mem0 + MongoDB).

    Uses SynthesisAgent to:
    - Query all research data
    - Recall related past research
    - Generate comprehensive report
    - Store synthesis
    """
    # Import agent only when activity executes (not in workflow sandbox)
    from agents import SynthesisAgent

    logger.info(f"Synthesizing research for run_id: {state.run_id}")

    db = MongoDBClient()
    await db.connect()
    try:
        agent = SynthesisAgent()
        synthesis = await agent.execute(state=state, db=db)

        synthesis_dict = synthesis.model_dump()

        logger.info(
            f"Research synthesis complete: {len(synthesis.main_findings)} findings"
        )
        return synthesis_dict
    finally:
        await db.disconnect()
