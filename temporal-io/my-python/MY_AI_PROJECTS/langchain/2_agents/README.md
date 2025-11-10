# Project 2: Research Assistant with Tavily MCP + MongoDB

## Overview

Automated research workflow using **AI agents with Tavily MCP** for real web search, integrated with MongoDB for persistent knowledge storage.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           Research Assistant Workflow                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ├──► 1. Query Parsing (Deterministic)
                          │
                          ├──► 2. Web Research Agent (AI Agent + Tavily MCP)
                          │         - Uses Tavily for REAL web search
                          │         - Stores results in MongoDB
                          │
                          └──► 3. Return Research Summary
```

## Key Features

### ✅ Real Tavily MCP Integration

This project uses **actual Tavily web search** via MCP (Model Context Protocol):

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

# Initialize Tavily MCP
mcp_client = MultiServerMCPClient({
    "tavily": {
        "transport": "streamable_http",
        "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
    }
})

# Get Tavily tools
tavily_tools = await mcp_client.get_tools(server_name="tavily")

# Create agent with Tavily tools
agent = create_agent(
    llm,
    tools=tavily_tools,  # Real web search tools!
    system_prompt="You are a research assistant..."
)
```

### ✅ MongoDB Knowledge Base

All research is stored in MongoDB for future reference:

```javascript
// research_sources collection
{
  "_id": "source_id",
  "type": "web",
  "title": "Article Title",
  "url": "https://...",
  "key_facts": [...],
  "credibility_score": 0.92,
  "topics": ["AI", "research"],
  "query_id": "session_id",
  "date_collected": "2024-11-01T..."
}
```

## Running the Workflow

### Prerequisites

1. **Temporal server** running on `localhost:7233`
2. **MongoDB** running on `localhost:27017`
3. **Tavily API key** in `.env` file

### Setup

```bash
# 1. Ensure services are running
docker ps  # Check Temporal and MongoDB

# 2. Set up environment
cp ../.env.example ../.env
# Add your TAVILY_API_KEY to .env

# 3. Activate virtual environment
source ../.venv/bin/activate
```

### Start the Worker

```bash
cd 2_agents
python main.py worker
```

### Execute the Workflow

In another terminal:

```bash
cd 2_agents
python main.py
```

## How It Works

### 1. Query Parsing (Deterministic)
- Extracts key terms from the query
- Identifies query type (academic, web, general)
- Checks for related past research in MongoDB

### 2. Web Research Agent (AI + Tavily MCP)

The agent:
1. **Receives the query** with key terms
2. **Uses Tavily MCP tool** to search the web
3. **Tavily returns real search results**:
   - Title, URL, content snippet
   - Relevance score
   - Multiple credible sources
4. **Agent analyzes** the results
5. **Stores in MongoDB**:
   - Source metadata
   - Key facts extracted
   - Credibility scores
6. **Returns summary** with agent's analysis

### 3. Result Compilation
- Aggregates all sources found
- Combines Tavily's answer with agent's analysis
- Returns structured research results

## Example Output

```
================================================================================
RESEARCH ASSISTANT WORKFLOW COMPLETED
================================================================================

Session ID: a3c5e7b9d2f1
Query: What are the latest developments in large language models?

Query Context:
  Type: academic
  Key Terms: latest, developments, large, language, models

Sources Found: 4

Summary:
Search Results: Recent developments in LLMs include GPT-4, Claude 3, and
multimodal capabilities. Key advances in efficiency and reasoning.

Agent Analysis: Based on the web search results, there have been significant
advancements in large language models over the past year, particularly in
areas of multimodal understanding, efficiency improvements, and reasoning
capabilities.

Top Sources:
  1. Advances in Large Language Models 2024
     URL: https://arxiv.org/...
     Credibility: 0.95
  2. GPT-4 and Claude 3: A Comparison
     URL: https://towardsdatascience.com/...
     Credibility: 0.88
================================================================================
```

## MongoDB Data

After running the workflow, check MongoDB:

```bash
docker exec -it <mongo_container> mongosh

> use langchain_temporal
> db.research_sources.find().pretty()
```

You'll see:
- All sources from Tavily
- Key facts extracted
- Credibility scores
- Query associations

## What Makes This Different from Project 1

| Aspect | Project 1 (LLM) | Project 2 (Agent + MCP) |
|--------|----------------|------------------------|
| **Pattern** | Direct LLM calls | AI Agent with tools |
| **Data Source** | LLM's training data | Real-time web search (Tavily) |
| **Tools** | None | Tavily MCP for web search |
| **Storage** | None | MongoDB knowledge base |
| **Use Case** | Content generation | Information retrieval |

## Tavily MCP vs Simulated Search

This implementation uses **real Tavily MCP**:
- ✅ Actual web search
- ✅ Current information (not limited to training cutoff)
- ✅ Credible sources with URLs
- ✅ Relevance scoring
- ✅ Up-to-date data

## Next Steps

Future enhancements:
- Add Academia MCP for peer-reviewed papers
- Implement knowledge graph builder
- Add synthesis agent for multi-source analysis
- Integrate ElevenLabs for audio report generation
- Add caching layer to avoid duplicate searches

## Troubleshooting

### "TAVILY_API_KEY not set"
```bash
# Check .env file
cat ../.env | grep TAVILY

# Get API key from: https://tavily.com/
```

### Agent not finding results
- Check internet connectivity
- Verify Tavily API key is valid
- Check Tavily API quota/limits

### MongoDB connection errors
```bash
# Ensure MongoDB is running
docker ps | grep mongo

# Start if needed
docker run -d -p 27017:27017 mongo:latest
```

## Learn More

- **Tavily MCP**: https://docs.tavily.com/
- **MCP Protocol**: https://modelcontextprotocol.io/
- **Langchain MCP Adapters**: https://python.langchain.com/docs/integrations/mcp
