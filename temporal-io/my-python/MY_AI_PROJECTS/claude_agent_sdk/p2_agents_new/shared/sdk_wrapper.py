"""
Wrapper around Claude Agent SDK for different usage patterns.

This module provides three main patterns:
1. Simple LLM calls without tools (query function)
2. Single agent with tools (Agent class)
3. Multi-agent coordination (SupervisorTeam class)
"""

import logging
from typing import List, Optional

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

from .mcp_config import get_mcp_servers

logger = logging.getLogger(__name__)


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

        logger.info(f"Agent '{self.name}' querying: {prompt}...")

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
                    logger.info(
                        f"Agent '{self.name}' cost: ${message.total_cost_usd:.4f}"
                    )

        return "\n".join(response_parts)
