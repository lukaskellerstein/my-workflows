"""MCP server configurations for research agents."""

import os
from typing import Dict, Any


def get_tavily_config() -> Dict[str, Any]:
    """Get Tavily MCP server configuration."""
    api_key = os.getenv("TAVILY_API_KEY", "")
    return {
        "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={api_key}",
        }
    }


def get_e2b_config() -> Dict[str, Any]:
    """Get E2B MCP server configuration."""
    api_key = os.getenv("E2B_API_KEY", "")
    return {
        "e2b-mcp-server": {
            "command": "uvx",
            "args": ["e2b-mcp-server"],
            "env": {"E2B_API_KEY": api_key},
        }
    }


def get_academia_config() -> Dict[str, Any]:
    """Get Academia MCP server configuration."""
    return {
        "academia": {
            "command": "python3",
            "args": ["-m", "academia_mcp", "--transport", "stdio"],
        }
    }


def get_elevenlabs_config() -> Dict[str, Any]:
    """Get ElevenLabs MCP server configuration."""
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    return {
        "elevenlabs": {
            "command": "uvx",
            "args": ["elevenlabs-mcp"],
            "env": {"ELEVENLABS_API_KEY": api_key},
        }
    }


# Note: MCP adapters for Langchain may not support all these MCP servers yet.
# For this demo, we'll create custom tool wrappers where needed.
