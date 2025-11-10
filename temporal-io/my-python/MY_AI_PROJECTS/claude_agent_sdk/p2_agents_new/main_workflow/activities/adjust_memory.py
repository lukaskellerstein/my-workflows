import logging
from typing import Dict

from temporalio import activity

from main_workflow.state import WorkflowState

logger = logging.getLogger(__name__)


@activity.defn
async def adjust_memory(state: WorkflowState) -> Dict:
    """
    Activity 1: Store user query in long-term memory (AI Agent + Mem0).

    Uses AdjustMemoryAgent to:
    - Store research query in Mem0
    - Tag with relevant topics
    - Make searchable for future queries
    """
    # Import agent only when activity executes (not in workflow sandbox)
    from agents import AdjustMemoryAgent

    logger.info(f"Storing query in memory for run_id: {state.run_id}")

    agent = AdjustMemoryAgent()
    result = await agent.execute(state=state)

    logger.info(f"Memory storage complete for query: {state.query}...")
    return result
