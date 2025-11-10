# AI Agent Pattern in Project 2

## ✅ Now Using `create_agent` Properly

Project 2 has been updated to **properly use Langchain agents** with tools, not just LLM calls.

## Key Changes

### Before (Wrong - Just LLM)
```python
# This was just an LLM call with structured output
llm_with_structure = llm.with_structured_output(ResearchFindings)
result = await llm_with_structure.ainvoke(conversation)
```

### After (Correct - Real Agent with Tools) ✅
```python
from langchain.agents import create_agent
from langchain.tools import tool

# 1. Define a tool
@tool(
    "simulate_web_search",
    description="Simulate a web search and return research sources."
)
def simulate_web_search(query: str, key_terms: str) -> str:
    # In production, this would call Tavily MCP
    results = {
        "sources": [...],
        "summary": "..."
    }
    return json.dumps(results)

# 2. Create agent with the tool
agent = create_agent(
    llm,
    tools=[simulate_web_search],
    system_prompt="You are a research assistant. Use tools to search and analyze."
)

# 3. Invoke the agent
result = await agent.ainvoke({
    "messages": [
        {
            "role": "user",
            "content": "Research: What are LLMs?"
        }
    ]
})

# 4. Extract tool results
messages = result.get("messages", [])
for msg in messages:
    if msg.__class__.__name__ == 'ToolMessage':
        # Parse the tool's JSON result
        tool_data = json.loads(msg.content)
```

## Why This Matters

### Project 1: LLM Calls
- **Purpose**: Content analysis and SEO optimization
- **Pattern**: Direct LLM invocation with structured output
- **Use case**: When you need AI to **generate/analyze** something

```python
# Project 1 pattern
llm_with_structure = llm.with_structured_output(Schema)
result = await llm_with_structure.ainvoke(conversation)
```

### Project 2: AI Agents
- **Purpose**: Research with tool use
- **Pattern**: Agent that can use tools to gather information
- **Use case**: When you need AI to **take actions** (search, fetch, compute)

```python
# Project 2 pattern
agent = create_agent(llm, tools=[my_tool], system_prompt="...")
result = await agent.ainvoke({"messages": [...]})
```

## The Difference

| Aspect | LLM Call (Project 1) | Agent (Project 2) |
|--------|---------------------|-------------------|
| **Tools** | No tools | Has tools it can invoke |
| **Action** | Generate/analyze | Search/fetch/compute |
| **Control Flow** | Single invoke | Multi-step reasoning + tool calls |
| **Output** | Structured data | Tool results + analysis |
| **Use Case** | Content creation | Information retrieval |

## Real World Example

### Scenario: Research AI Agents

**With LLM (Project 1 pattern)**:
```python
# LLM generates based on its training data (might be outdated)
llm_with_structure = llm.with_structured_output(ResearchSchema)
result = await llm_with_structure.ainvoke([
    {"role": "user", "content": "What are the latest AI agent frameworks?"}
])
# Result: Generated from Claude's training data (cutoff Jan 2025)
```

**With Agent (Project 2 pattern)**:
```python
# Agent uses Tavily tool to search the web for current info
agent = create_agent(llm, tools=[tavily_search], ...)
result = await agent.ainvoke({
    "messages": [{"role": "user", "content": "What are the latest AI agent frameworks?"}]
})
# Agent thinks: "I should use tavily_search to find current information"
# Agent calls: tavily_search("latest AI agent frameworks 2025")
# Agent receives: Current search results from the web
# Agent responds: Analysis based on current web data
```

## Tool Definition Pattern

### Custom Tool
```python
@tool(
    "tool_name",
    description="What this tool does. Be specific for the LLM to understand when to use it."
)
def tool_name(param1: str, param2: int) -> str:
    """
    Detailed docstring for developers.

    Args:
        param1: Description
        param2: Description

    Returns:
        Description of return value (usually JSON string)
    """
    # Implementation
    result = {"data": "..."}
    return json.dumps(result)  # Always return string (often JSON)
```

### MCP Tool (Future)
```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "tavily": {
        "transport": "streamable_http",
        "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=..."
    }
})

tools = await client.get_tools(server_name="tavily")

agent = create_agent(llm, tools=tools, system_prompt="...")
```

## Agent Flow

1. **User asks a question** → Agent receives message
2. **Agent thinks** → "I need to search for this"
3. **Agent calls tool** → `simulate_web_search(query="...")`
4. **Tool executes** → Returns JSON data
5. **Agent receives result** → Sees ToolMessage with data
6. **Agent analyzes** → Processes the tool result
7. **Agent responds** → Provides answer based on tool data

## Message Types in Agent Response

```python
result = await agent.ainvoke({...})
messages = result["messages"]

# Message types:
# 1. HumanMessage - original user input
# 2. AIMessage - agent's thoughts/tool decisions (has tool_calls)
# 3. ToolMessage - results from tool execution
# 4. AIMessage - agent's final response
```

## ✅ Production: Using Real Tavily MCP (Implemented!)

```python
# ✅ Project 2 NOW uses real Tavily MCP!
from langchain_mcp_adapters.client import MultiServerMCPClient
import os

# Get API key
tavily_api_key = os.getenv("TAVILY_API_KEY")

# Initialize Tavily MCP client
mcp_client = MultiServerMCPClient({
    "tavily": {
        "transport": "streamable_http",
        "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_api_key}"
    }
})

# Get real Tavily tools
tavily_tools = await mcp_client.get_tools(server_name="tavily")

# Create agent with REAL web search capability
agent = create_agent(
    llm,
    tools=tavily_tools,  # Real Tavily search tools!
    system_prompt="You are a research assistant. Use Tavily to search the web."
)

# Agent now performs REAL web searches!
result = await agent.ainvoke({
    "messages": [{"role": "user", "content": "Search for latest AI news"}]
})

# Agent will:
# 1. Call Tavily search tool
# 2. Get real web results
# 3. Analyze and summarize
```

## Summary

✅ **Project 1** = LLM calls for generation/analysis
✅ **Project 2** = AI agents with tools for action/retrieval
✅ **Project 3** = Multi-agent teams (multiple agents collaborating)
✅ **Project 4** = All patterns combined

The key distinction: **Agents have tools, LLMs don't.**
