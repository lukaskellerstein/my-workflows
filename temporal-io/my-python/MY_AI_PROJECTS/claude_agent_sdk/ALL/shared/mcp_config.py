"""MCP Server Configurations for Claude Agent SDK Integration."""

import os
from claude_agent_sdk.types import (
    McpStdioServerConfig,
    McpSSEServerConfig,
    McpHttpServerConfig,
    McpServerConfig,
)

# API Keys from environment variables
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")
E2B_API_KEY = os.getenv("E2B_API_KEY", "e2b_185bf1ec07e37cb14efcf2bb592e92feb9b3ea41")
OPENMEMORY_API_KEY = os.getenv("OPENMEMORY_API_KEY", "om-9pasijokujjgzsw2mhwyourn1234zwbx")
ELEVENLABS_API_KEY = os.getenv(
    "ELEVENLABS_API_KEY", "sk_2ccc539363f5f25c5201c40d356df73ce785f59c193dab75"
)
MONGODB_CONNECTION_STRING = os.getenv(
    "MONGODB_CONNECTION_STRING", "mongodb://localhost:27017/myTemporalAgentsDB"
)


# Tavily Search - Uses HTTP transport
tavily_config: McpHttpServerConfig = {
    "type": "http",
    "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}",
}

# E2B - Uses stdio transport
e2b_config: McpStdioServerConfig = {
    "type": "stdio",
    "command": "uvx",
    "args": ["e2b-mcp-server"],
    "env": {"E2B_API_KEY": E2B_API_KEY},
}

# Mem0 (OpenMemory) - Uses stdio transport
mem0_config: McpStdioServerConfig = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "supergateway", "--sse", "http://127.0.0.1:8765/mcp/claude/sse/lukas"],
}

# MongoDB - Uses stdio transport
mongodb_config: McpStdioServerConfig = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "mongodb-mcp-server@latest"],
    "env": {"MDB_MCP_CONNECTION_STRING": MONGODB_CONNECTION_STRING},
}

# MinIO - Uses HTTP transport (Docker Compose service with streamable HTTP endpoint)
minio_config: McpHttpServerConfig = {
    "type": "http",
    "url": "http://localhost:8090/mcp",
}

# ArXiv - Uses stdio transport
arxiv_config: McpStdioServerConfig = {
    "type": "stdio",
    "command": "uv",
    "args": [
        "tool",
        "run",
        "arxiv-mcp-server",
        "--storage-path",
        "/tmp/arxiv_papers_claude_agents",
    ],
}

# ElevenLabs - Uses stdio transport
elevenlabs_config: McpStdioServerConfig = {
    "type": "stdio",
    "command": "uvx",
    "args": ["elevenlabs-mcp"],
    "env": {
        "ELEVENLABS_API_KEY": ELEVENLABS_API_KEY,
        "ELEVENLABS_MCP_BASE_PATH": "/home/lukas/Temp/elevenlabs-files",
        "ELEVENLABS_MCP_OUTPUT_MODE": "files",  # Save files to disk
    },
}


# Master MCP server registry
# Maps server names to their configurations
MCP_SERVERS: dict[str, McpServerConfig] = {
    "tavily": tavily_config,
    "e2b": e2b_config,
    "openmemory": mem0_config,
    "mongodb": mongodb_config,
    "minio": minio_config,
    "arxiv": arxiv_config,
    "elevenlabs": elevenlabs_config,
}


def get_mcp_servers(*server_names: str) -> dict[str, McpServerConfig]:
    """
    Get MCP server configurations by name.

    Args:
        *server_names: Names of MCP servers to retrieve

    Returns:
        Dictionary mapping server names to their configurations

    Example:
        >>> configs = get_mcp_servers("tavily", "e2b")
        >>> # Use in Agent or SupervisorTeam

    Note:
        Tool permissions are granted using the pattern: mcp__<server_name>
        This grants access to ALL tools from that MCP server.
        For example, "mcp__tavily" grants access to all Tavily tools.
    """
    return {name: MCP_SERVERS[name] for name in server_names if name in MCP_SERVERS}
