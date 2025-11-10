import logging

from shared.sdk_wrapper import Agent

from main_workflow.state import WorkflowState

logger = logging.getLogger(__name__)


class AdjustMemoryAgent:
    """Agent for storing user queries and research context in long-term memory (Mem0)."""

    def __init__(self):
        self.logger = logging.getLogger("agent.adjust_memory")

    async def execute(self, state: WorkflowState) -> dict:
        """
        Store user query and research context in Mem0 for future reference.

        Args:
            state: Workflow state with query and run_id

        Returns:
            Dictionary with memory storage result
        """
        self.logger.info(
            f"Storing research context in memory for run_id: {state.run_id}"
        )

        # Use SDK Agent with Mem0 MCP for memory storage
        async with Agent(
            name="memory_manager",
            description="Memory management specialist with access to OpenMemory.",
            system_prompt="""You are a memory management agent with access to OpenMemory.

Your job is to store important information about research queries for future reference.

When given a research query, use the OpenMemory tools to:
1. Store the query and context using store_memory
2. Tag it appropriately for future retrieval
3. Create searchable memories that can help with similar future queries

Focus on:
- The main topic being researched
- Key search terms and concepts
- User intent and research goals
- Timestamp and session information

Return a simple confirmation message when done.""",
            mcp_servers=["openmemory"],
        ) as agent:

            prompt = f"""Store this research query in long-term memory:

QUERY: {state.query}
RUN_ID: {state.run_id}
TIMESTAMP: Now

Please:
1. Use store_memory to save this query
2. Tag it with relevant topics
3. Make it searchable for future similar queries

Confirm when complete."""

            response_text = await agent.query(prompt)

        self.logger.info(f"Memory storage complete: {response_text}")

        result = {
            "success": True,
            "run_id": state.run_id,
            "query": state.query,
            "memory_response": response_text,  # First 500 chars
        }

        return result
