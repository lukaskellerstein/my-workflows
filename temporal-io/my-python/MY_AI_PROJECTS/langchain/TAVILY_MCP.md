# Tavily MCP Integration - Project 2

## ✅ REAL Tavily MCP Implementation

Project 2 now uses **actual Tavily MCP** for real-time web search, not simulated data.

## What Changed

### Before (Wrong) ❌
```python
# Simulated tool - fake data
@tool("simulate_web_search")
def simulate_web_search(query: str) -> str:
    return json.dumps({"sources": [...]})  # Fake data
```

### Now (Correct) ✅
```python
from langchain_mcp_adapters.client import MultiServerMCPClient

# Initialize REAL Tavily MCP
mcp_client = MultiServerMCPClient({
    "tavily": {
        "transport": "streamable_http",
        "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={api_key}"
    }
})

# Get REAL Tavily tools
tavily_tools = await mcp_client.get_tools(server_name="tavily")

# Agent uses REAL web search
agent = create_agent(llm, tools=tavily_tools, ...)
```

## How Tavily MCP Works

### 1. MCP Client Initialization
```python
mcp_client = MultiServerMCPClient({
    "tavily": {
        "transport": "streamable_http",  # HTTP transport for Tavily
        "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=..."
    }
})
```

### 2. Get Tools from MCP Server
```python
# Tavily MCP provides search tools
tavily_tools = await mcp_client.get_tools(server_name="tavily")

# Tools returned:
# - tavily_search: Web search tool
# - Other Tavily capabilities
```

### 3. Agent Uses Tools
```python
agent = create_agent(llm, tools=tavily_tools, ...)

# When agent invokes:
result = await agent.ainvoke({
    "messages": [{"role": "user", "content": "Search for AI news"}]
})

# Agent thinks: "I should use tavily_search tool"
# Agent calls: tavily_search(query="AI news")
# Tavily MCP: Makes REAL web search via Tavily API
# Returns: Real search results
```

### 4. Parse Tavily Results
```python
# Tavily returns structured data:
{
    "results": [
        {
            "title": "Actual article title",
            "url": "https://real-url.com/article",
            "content": "Real article snippet...",
            "score": 0.92  # Relevance score
        },
        ...
    ],
    "answer": "Tavily's AI-generated answer from sources"
}
```

## Complete Implementation

### File: `2_agents/activities/agent_activities/web_research_agent.py`

```python
import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic

async def research_web_sources(query, key_terms, session_id, mongodb_uri, db_name):
    # 1. Get Tavily API key from environment
    tavily_api_key = os.getenv("TAVILY_API_KEY")

    # 2. Initialize Tavily MCP client
    mcp_client = MultiServerMCPClient({
        "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_api_key}"
        }
    })

    # 3. Get Tavily tools
    tavily_tools = await mcp_client.get_tools(server_name="tavily")

    # 4. Create agent with Tavily tools
    llm = ChatAnthropic(model="claude-sonnet-4-20250514")
    agent = create_agent(
        llm,
        tools=tavily_tools,
        system_prompt="Use Tavily to search the web for credible sources."
    )

    # 5. Invoke agent
    agent_response = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": f"Search for: {query}"
        }]
    })

    # 6. Parse Tavily results from ToolMessage
    messages = agent_response.get("messages", [])
    for msg in messages:
        if msg.__class__.__name__ == 'ToolMessage':
            # This contains REAL Tavily search results!
            tavily_data = json.loads(msg.content)
            results = tavily_data.get("results", [])

            # Process real web results
            for result in results:
                source = {
                    "title": result["title"],
                    "url": result["url"],
                    "content": result["content"],
                    "score": result["score"]
                }
                # Store in MongoDB
                mongo_client.add_source(source)

    return research_results
```

## Required Setup

### 1. Get Tavily API Key

Sign up at: https://tavily.com/

### 2. Add to .env

```bash
TAVILY_API_KEY=tvly-your-actual-api-key-here
```

### 3. Install Dependencies

Already in pyproject.toml:
```toml
dependencies = [
    "langchain-mcp-adapters>=0.1.0",
    ...
]
```

## Benefits of Real Tavily MCP

| Aspect | Simulated | Real Tavily MCP |
|--------|-----------|----------------|
| **Data** | Fake | Real-time web data |
| **Sources** | Made up | Actual URLs |
| **Freshness** | Static | Current information |
| **Credibility** | Fake scores | Real relevance scores |
| **Use Case** | Demo only | Production ready |

## Tavily MCP vs Direct API

### Why MCP Instead of Direct Tavily API?

#### Direct Tavily API
```python
import requests

response = requests.post(
    "https://api.tavily.com/search",
    json={"query": "..."},
    headers={"Authorization": f"Bearer {api_key}"}
)
# Manual parsing, integration, error handling
```

#### Tavily MCP ✅
```python
from langchain_mcp_adapters.client import MultiServerMCPClient

mcp_client = MultiServerMCPClient({"tavily": {...}})
tools = await mcp_client.get_tools(server_name="tavily")
agent = create_agent(llm, tools=tools, ...)

# MCP handles:
# - Tool discovery
# - Parameter validation
# - Error handling
# - Response parsing
# - Agent integration
```

## Advantages of MCP Pattern

1. **Standardized Interface**: All MCP servers use same protocol
2. **Easy Tool Discovery**: `get_tools()` discovers capabilities
3. **Agent Integration**: Tools work seamlessly with agents
4. **Multiple Servers**: Can add Academia, E2B, etc. easily
5. **Type Safety**: Tools include schemas and validation

## Adding More MCP Servers

### Academia MCP (for academic papers)
```python
mcp_client = MultiServerMCPClient({
    "tavily": {...},
    "academia": {
        "command": "python3",
        "args": ["-m", "academia_mcp", "--transport", "stdio"]
    }
})

# Get tools from both
tavily_tools = await mcp_client.get_tools(server_name="tavily")
academia_tools = await mcp_client.get_tools(server_name="academia")

# Agent can use both!
agent = create_agent(llm, tools=tavily_tools + academia_tools, ...)
```

### E2B MCP (for code execution)
```python
mcp_client = MultiServerMCPClient({
    "tavily": {...},
    "e2b": {
        "command": "uvx",
        "args": ["e2b-mcp-server"],
        "env": {"E2B_API_KEY": "..."}
    }
})
```

## Testing

### Test with real query:

```bash
cd 2_agents
python main.py

# Agent will:
# 1. Connect to Tavily MCP
# 2. Perform REAL web search
# 3. Return actual results
# 4. Store in MongoDB
```

### Check MongoDB for real data:

```bash
docker exec -it <mongo> mongosh
> use langchain_temporal
> db.research_sources.find().pretty()

# You'll see REAL web sources!
```

## Troubleshooting

### "TAVILY_API_KEY not set"
```bash
echo $TAVILY_API_KEY  # Should show your key
# Or check .env file
cat .env | grep TAVILY
```

### "Connection to MCP server failed"
- Check internet connection
- Verify API key is valid
- Check Tavily API status: https://status.tavily.com/

### "No results returned"
- Check query is not too specific
- Verify Tavily API quota (free tier limits)
- Check agent logs for tool invocation

## Documentation

- **Tavily API**: https://docs.tavily.com/
- **MCP Protocol**: https://modelcontextprotocol.io/
- **Langchain MCP**: https://python.langchain.com/docs/integrations/mcp

## Summary

✅ Project 2 uses **REAL Tavily MCP**
✅ **Real-time web search** (not simulated)
✅ **Production-ready** implementation
✅ **MongoDB storage** of real sources
✅ **Scalable pattern** for adding more MCP servers

The implementation follows the original requirements to use Tavily via MCP! 🎉
