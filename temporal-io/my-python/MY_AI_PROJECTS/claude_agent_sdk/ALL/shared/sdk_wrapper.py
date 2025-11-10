"""
Wrapper around Claude Agent SDK for different usage patterns.

This module provides three main patterns:
1. Simple LLM calls without tools (query function)
2. Single agent with tools (Agent class)
3. Multi-agent coordination (SupervisorTeam class)
"""

import logging
from typing import Any, Dict, List, Optional

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    query as sdk_query,
    tool,
)
from claude_agent_sdk.types import McpServerConfig

from .mcp_config import get_mcp_servers

logger = logging.getLogger(__name__)


# ==============================================================================
# Pattern 1: Simple LLM Call (No Tools)
# ==============================================================================


async def simple_query(prompt: str, system_prompt: Optional[str] = None) -> str:
    """
    Make a simple LLM call without any tools.

    Args:
        prompt: User prompt
        system_prompt: Optional system prompt

    Returns:
        Claude's text response

    Example:
        >>> response = await simple_query("What is 2+2?")
        >>> print(response)
        "4"
    """
    logger.info(f"Simple query: {prompt[:50]}...")

    options = ClaudeAgentOptions(
        system_prompt=system_prompt or "You are a helpful assistant.",
        model="claude-sonnet-4-5-20250929",
    )

    response_text = []

    # Using sdk_query for stateless requests
    async for message in sdk_query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    response_text.append(block.text)
        elif isinstance(message, ResultMessage):
            if message.total_cost_usd:
                logger.info(f"Query cost: ${message.total_cost_usd:.4f}")

    return "\n".join(response_text)


# ==============================================================================
# Pattern 2: Single Agent (With Optional Tools)
# ==============================================================================


class Agent:
    """
    Single agent that can have custom tools and memory.

    This is a wrapper around ClaudeSDKClient for stateful conversations.
    """

    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[str]] = None,
        mcp_servers: Optional[List[str]] = None,
    ):
        """
        Initialize an agent.

        Args:
            name: Agent name
            description: Agent description
            system_prompt: System prompt for the agent
            tools: List of allowed tools (e.g., ["Read", "Write", "Bash"])
            mcp_servers: List of MCP server names to enable (e.g., ["tavily", "e2b"])

        Example:
            >>> agent = Agent(
            ...     name="researcher",
            ...     description="Research agent",
            ...     tools=["Read", "Grep"],
            ...     mcp_servers=["tavily"],
            ... )
        """
        self.name = name
        self.description = description
        self.system_prompt = system_prompt or description
        self.tools = tools or []

        # Convert MCP server names to configurations
        if mcp_servers:
            self.mcp_server_configs = get_mcp_servers(*mcp_servers)
            # Grant access to all tools from MCP servers using mcp__<server_name> pattern
            for server_name in mcp_servers:
                self.tools.append(f"mcp__{server_name}")
        else:
            self.mcp_server_configs = {}

        self.client: Optional[ClaudeSDKClient] = None
        self.session_id: Optional[str] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Connect the agent (start the SDK client)."""

        print("------------ AGENT CONFIGURATION -----------")
        print(self.tools)
        print(self.mcp_server_configs)
        print("-------------------------------------------")

        options = ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            model="claude-sonnet-4-5-20250929",
            allowed_tools=self.tools if self.tools else None,
            mcp_servers=self.mcp_server_configs if self.mcp_server_configs else None,
            resume=self.session_id,  # Resume previous session if exists
        )

        self.client = ClaudeSDKClient(options=options)
        await self.client.connect()
        logger.info(
            f"Agent '{self.name}' connected with MCP servers: {list(self.mcp_server_configs.keys())}"
        )

    async def disconnect(self) -> None:
        """Disconnect the agent."""
        if self.client:
            await self.client.disconnect()
            logger.info(f"Agent '{self.name}' disconnected")

    async def query(self, prompt: str) -> str:
        """
        Send a query to the agent.

        Args:
            prompt: User prompt

        Returns:
            Agent's response text

        Example:
            >>> async with Agent("researcher", "Research agent") as agent:
            ...     response = await agent.query("Find information about...")
        """
        if not self.client:
            raise RuntimeError(
                f"Agent '{self.name}' not connected. Use async with or call connect()"
            )

        logger.info(f"Agent '{self.name}' querying: {prompt[:50]}...")

        await self.client.query(prompt)

        response_parts = []
        async for message in self.client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)
                    elif isinstance(block, ToolUseBlock):
                        logger.info(f"Agent '{self.name}' using tool: {block.name}")
            elif isinstance(message, ResultMessage):
                # Save session ID for potential resumption
                self.session_id = message.session_id
                if message.total_cost_usd:
                    logger.info(f"Agent '{self.name}' cost: ${message.total_cost_usd:.4f}")

        return "\n".join(response_parts)


# ==============================================================================
# Pattern 3: Multi-Agent Team (Supervisor Pattern)
# ==============================================================================


class SupervisorTeam:
    """
    Multi-agent team coordinated by a supervisor agent.

    The supervisor delegates tasks to specialist agents and synthesizes results.
    """

    def __init__(
        self,
        supervisor_name: str,
        supervisor_description: str,
        team_agents: Dict[str, AgentDefinition],
        supervisor_tools: Optional[List[str]] = None,
        mcp_servers: Optional[List[str]] = None,
    ):
        """
        Initialize supervisor team.

        Args:
            supervisor_name: Name of supervisor agent
            supervisor_description: Description of supervisor's role
            team_agents: Dictionary of {agent_name: AgentDefinition}
            supervisor_tools: Tools available to supervisor
            mcp_servers: List of MCP server names to enable for all agents

        Example:
            >>> team = SupervisorTeam(
            ...     supervisor_name="lead",
            ...     supervisor_description="Technical lead",
            ...     team_agents={
            ...         "researcher": AgentDefinition(
            ...             description="Research specialist",
            ...             prompt="You research topics",
            ...             tools=["Read", "Grep"],
            ...         ),
            ...     },
            ...     mcp_servers=["tavily"],
            ... )
        """
        self.supervisor_name = supervisor_name
        self.supervisor_description = supervisor_description
        self.team_agents = team_agents
        self.supervisor_tools = supervisor_tools or ["Read", "Grep"]

        # Convert MCP server names to configurations
        if mcp_servers:
            self.mcp_server_configs = get_mcp_servers(*mcp_servers)
        else:
            self.mcp_server_configs = {}

        # Create supervisor definition
        self.supervisor_definition = AgentDefinition(
            description=supervisor_description,
            prompt=f"You are {supervisor_name}. {supervisor_description}",
            tools=self.supervisor_tools,
            model="sonnet",
        )

    async def execute(self, task: str, max_iterations: int = 10) -> str:
        """
        Execute a task using the supervisor pattern.

        Args:
            task: The task to accomplish
            max_iterations: Maximum number of delegation cycles

        Returns:
            Final result from supervisor

        Example:
            >>> result = await team.execute("Research and analyze...")
        """
        logger.info(f"Supervisor team '{self.supervisor_name}' executing task")

        # Build team descriptions
        team_info = "\n".join(
            [f"- {name}: {defn.description}" for name, defn in self.team_agents.items()]
        )

        # Create options with all agents
        all_agents = {self.supervisor_name: self.supervisor_definition}
        all_agents.update(self.team_agents)

        options = ClaudeAgentOptions(
            agents=all_agents,
            system_prompt=f"You are {self.supervisor_name}. {self.supervisor_description}",
            model="claude-sonnet-4-5-20250929",
            mcp_servers=self.mcp_server_configs if self.mcp_server_configs else None,
        )

        logger.info(
            f"SupervisorTeam '{self.supervisor_name}' initialized with MCP servers: {list(self.mcp_server_configs.keys())}"
        )

        result = ""

        async with ClaudeSDKClient(options=options) as client:
            # Initial supervisor prompt
            supervisor_prompt = f"""You are a supervisor managing a team of specialized agents.

Your responsibility:
{self.supervisor_description}

Your team members:
{team_info}

Task to accomplish:
{task}

As the supervisor, you should:
1. Analyze the task and decide if you can handle it directly or need to delegate
2. If delegating, clearly specify which team member should handle which part
3. Collect results from team members
4. Synthesize the final answer for the user

When you need to delegate work, use this format:
DELEGATE TO: [agent-name]
TASK: [specific task for that agent]

When you have the final answer, use this format:
FINAL ANSWER:
[your answer to the user]
"""

            await client.query(supervisor_prompt)

            # Process supervisor's decision-making
            iteration = 0

            while iteration < max_iterations:
                supervisor_response = []

                async for msg in client.receive_response():
                    if isinstance(msg, AssistantMessage):
                        for block in msg.content:
                            if isinstance(block, TextBlock):
                                logger.info(f"Supervisor: {block.text[:100]}...")
                                supervisor_response.append(block.text)
                    elif isinstance(msg, ResultMessage):
                        if msg.total_cost_usd:
                            logger.info(f"Iteration {iteration} cost: ${msg.total_cost_usd:.4f}")

                response_text = "\n".join(supervisor_response)

                # Check for final answer
                if "FINAL ANSWER:" in response_text:
                    result = response_text.split("FINAL ANSWER:")[1].strip()
                    break

                # Check for delegation
                if "DELEGATE TO:" in response_text:
                    delegation = self._parse_delegation(response_text)
                    if delegation:
                        agent_name, agent_task = delegation
                        logger.info(f"Delegating to {agent_name}: {agent_task[:50]}...")

                        # Execute with team member using subagent call
                        agent_prompt = f"""Execute this task as {agent_name}:
{agent_task}

Report your findings back to the supervisor."""

                        await client.query(agent_prompt)
                        iteration += 1
                    else:
                        # Could not parse, treat as final
                        result = response_text
                        break
                else:
                    # No delegation marker, treat as final answer
                    result = response_text
                    break

        return result

    def _parse_delegation(self, text: str) -> Optional[tuple[str, str]]:
        """Parse delegation request from supervisor's response."""
        try:
            lines = text.split("\n")
            agent_name = None
            task = None

            for i, line in enumerate(lines):
                if "DELEGATE TO:" in line:
                    agent_name = line.split("DELEGATE TO:")[1].strip()
                elif "TASK:" in line and agent_name:
                    task_lines = [line.split("TASK:")[1].strip()]
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() and not lines[j].startswith(("DELEGATE", "FINAL")):
                            task_lines.append(lines[j].strip())
                        else:
                            break
                    task = " ".join(task_lines)
                    break

            if agent_name and task and agent_name in self.team_agents:
                return (agent_name, task)

            return None
        except Exception as e:
            logger.error(f"Failed to parse delegation: {e}")
            return None


# ==============================================================================
# Utility Functions
# ==============================================================================


def create_custom_tools(tool_definitions: List[dict]) -> dict:
    """
    Create custom MCP tools from definitions.

    Args:
        tool_definitions: List of tool definitions

    Returns:
        MCP server instance

    Example:
        >>> @tool("add", "Add numbers", {"a": float, "b": float})
        ... async def add_numbers(args):
        ...     return {"content": [{"type": "text", "text": str(args["a"] + args["b"])}]}
        ...
        >>> server = create_custom_tools([add_numbers])
    """
    # Tool definitions should be decorated with @tool already
    return create_sdk_mcp_server(
        name="custom_tools",
        version="1.0.0",
        tools=tool_definitions,
    )
