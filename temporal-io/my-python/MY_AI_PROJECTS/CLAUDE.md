write a CLAUDE.md file for a description below in a way that coding ai agent will clearly understand what he needs to implement. Replace section of `### workflow description` with a concerete description of the workflow based on my notes.

AI agent can use the MCPs listed below. Design workflows and tailor AI agents based on their capabilities.

# MCP list

## Tavily search

Tavily Search is an AI-powered search engine designed to deliver fast, accurate, and source-backed answers tailored for developers and AI applications.

```envVar
api_key=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
```

```json
{
  "mcpServers": {
      "tavily": {
        "transport": "streamable_http",
        "url": "https://mcp.tavily.com/mcp/?tavilyApiKey={api_key}"
    }
}
```

## E2B

The E2B MCP server allows you to add code interpreting capabilities to your Claude Desktop app via the E2B Sandbox.

```envVar
api_key=e2b_185bf1ec07e37cb14efcf2bb592e92feb9b3ea41
```

```json
{
  "mcpServers": {
    "e2b-mcp-server": {
      "command": "uvx",
      "args": ["e2b-mcp-server"],
      "env": { "E2B_API_KEY": "<api_key>" }
    }
  }
}
```

## Mem0

Mem0 is an open-source memory framework that enables AI agents to store, recall, and reason over past interactions to build long-term contextual awareness.

```envVar
api_key=om-9pasijokujjgzsw2mhwyourn1234zwbx
```

```json
{
  "mcpServers": {
      "tavily": {
        "command": "npx",
        "args": ["@openmemory/install", "--client", "claude"],
        "env": { "OPENMEMORY_API_KEY": "<api_key>" }
    }
}
```

## MongoDB

MongoDB is a document-oriented NoSQL database that stores data in flexible, JSON-like documents, allowing for scalable, schema-free data management.

```json
{
  "mcpServers": {
    "MongoDB": {
      "command": "npx",
      "args": ["-y", "mongodb-mcp-server@latest"],
      "env": {
        "MDB_MCP_CONNECTION_STRING": "mongodb://localhost:27017/myDatabase"
      }
    }
  }
}
```

## Academia

MCP server with tools to search, fetch, analyze, and report on scientific papers and datasets.

```json
{
  "mcpServers": {
    "academia": {
      "command": "python3",
      "args": ["-m", "academia_mcp", "--transport", "stdio"]
    }
  }
}
```

## ElevenLabs

ElevenLabs is an AI-powered platform that creates highly realistic and expressive synthetic voices for text-to-speech and voice cloning applications.

```envVar
api_key=sk_2ccc539363f5f25c5201c40d356df73ce785f59c193dab75
```

```json
{
  "mcpServers": {
    "ElevenLabs": {
      "command": "uvx",
      "args": ["elevenlabs-mcp"],
      "env": {
        "ELEVENLABS_API_KEY": "<api_key>"
      }
    }
  }
}
```

---

# Goal

Demonstrate a integration of `Claude Agent SDK` within `temporal.io` workflows. Implement projects described below. Use programming language `Python` and `uv`.

## Project 1

Folder: `1_llm_call`

### Workflow description

My description: A real-world workflow that will demonstrate a multiple nodes/activities with LLM calls. Some of the nodes/activities should not use LLM and be purely deterministic, some of them use LLM calls.

## Project 2

Folder: `2_agents`

### Workflow description

My description: A real-world workflow that will demonstrate a multiple nodes/activities with AI agents (with MCP tools). Some of the nodes/activities should not use AI agents and be purely deterministic, some of them use AI agents.

## Project 3

Folder: `3_multi-agents`

### Workflow description

My description: A real-world workflow that will demonstrate a multiple nodes/activities with `team of AI agents (with MCP tools)`. Some of the nodes/activities should not use `team of AI agents` and be purely deterministic, some of them use `team of AI agents`. By team of AI agents is meant that within one node/activity will be called the team of AI agents. Let's use either `supervision` patter or `swarm` pattern for the team of agents = multi-agent approach.

## Project 4

Folder: `4_all`

### Workflow description

My description: A real-world workflow that will demonstrate a multiple nodes/activities with `LLM` and `AI agents` and `team of AI agents (with MCP tools)`. Some of the nodes/activities should not use any of that and be purely deterministic, some of them use these. Thsi workflow should demonstrate a way how to cleverly combine all previous projects into a meaningful real-world workflow that is solving a real problem.
