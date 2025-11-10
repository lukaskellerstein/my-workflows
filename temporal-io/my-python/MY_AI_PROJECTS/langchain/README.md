# Langchain + Temporal.io Integration Projects

Comprehensive demonstration of integrating Langchain AI agents and LLMs within Temporal.io workflows for robust, fault-tolerant AI applications.

## Overview

This repository contains four progressive projects showcasing different patterns of AI integration:

1. **Project 1**: Content Publishing Pipeline (LLM Calls)
2. **Project 2**: Research Assistant (AI Agents + MongoDB)
3. **Project 3**: Code Review Pipeline (Multi-Agent Teams) - Stub
4. **Project 4**: Product Launch Automation (All Patterns) - Stub

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Temporal Workflows                        │
├─────────────────────────────────────────────────────────────┤
│  Deterministic  │  LLM Calls  │  AI Agents  │  Multi-Agent  │
│   Activities    │   (Claude)  │  (w/ MCP)   │    Teams      │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    Standard        Langchain     Langchain +    LangGraph +
    Python          Chat Models    MCP Tools      Patterns
```

## Tech Stack

- **Workflow Engine**: Temporal.io
- **AI Framework**: Langchain
- **Package Manager**: uv
- **Language**: Python 3.12+
- **LLM Providers**: Anthropic Claude, OpenAI
- **MCP Tools**: Tavily, E2B, Mem0, Academia, ElevenLabs
- **Database**: MongoDB (for knowledge persistence)

## Prerequisites

### 1. Install Temporal

```bash
# Using Docker
docker run -d -p 7233:7233 temporalio/auto-setup:latest
```

### 2. Install MongoDB (for Project 2)

```bash
# Using Docker
docker run -d -p 27017:27017 mongo:latest
```

### 3. Setup Python Environment

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
cd /path/to/project
uv venv
source .venv/bin/activate
uv sync
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required API keys:
- `ANTHROPIC_API_KEY` - For Claude LLM
- `OPENAI_API_KEY` - For OpenAI models (optional)
- `TAVILY_API_KEY` - For Tavily search (Project 2+)
- `E2B_API_KEY` - For E2B sandbox (Project 3+)
- `ELEVENLABS_API_KEY` - For voice generation (Project 4)
- `MONGODB_URI` - MongoDB connection string (Project 2+)

## Project Details

### Project 1: Content Publishing Pipeline

**Status**: ✅ Fully Implemented

Real-world workflow for publishing articles with AI-powered analysis and SEO.

**Features**:
- Input validation (deterministic)
- Content analysis using Claude
- SEO optimization using Claude
- Image processing (deterministic)
- Final publication (deterministic)

**Run**:
```bash
cd 1_llm_call
# Terminal 1: Start worker
python main.py worker

# Terminal 2: Execute workflow
python main.py
```

**Key Learning**: Integration of LLM calls with retry policies in Temporal workflows

---

### Project 2: Research Assistant with Tavily MCP + MongoDB

**Status**: ✅ Fully Implemented with Real Tavily MCP

Automated research workflow using AI agents with **real Tavily web search** and persistent MongoDB knowledge base.

**Features**:
- Query parsing (deterministic)
- **AI Agent with Tavily MCP for real web search** ⭐
- **MultiServerMCPClient for MCP integration**
- MongoDB for source storage and knowledge persistence
- Real-time web data (not limited to LLM training cutoff)
- Credibility scoring and source tracking

**Run**:
```bash
cd 2_agents
# Terminal 1: Start worker
python main.py worker

# Terminal 2: Execute workflow
python main.py
```

**Key Learning**: **Real Tavily MCP integration**, AI agents with tools, MongoDB persistence, current web data retrieval

---

### Project 3: Code Review Pipeline

**Status**: 🚧 Stub Implementation

Multi-agent code review using supervision pattern.

**Planned Features**:
- Supervisor agent coordinating specialists
- Security agent (E2B)
- Performance agent (E2B)
- Style agent (Academia MCP)
- Test generation agent (E2B)

**To Implement**: See `3_multi-agents/README.md`

**Key Learning**: Multi-agent coordination, supervision pattern, code analysis

---

### Project 4: Product Launch Automation

**Status**: 🚧 Stub Implementation

Comprehensive workflow combining all patterns for product launches.

**Planned Features**:
- Market research swarm (Tavily)
- Content generation (LLM)
- Media creation (ElevenLabs)
- Deployment automation (E2B)
- Monitoring (Mem0)
- Multi-agent analysis

**To Implement**: See `4_all/README.md`

**Key Learning**: Complete AI workflow orchestration, all patterns combined

## Key Concepts Demonstrated

### 1. Deterministic vs Non-Deterministic Activities

Temporal requires workflow code to be deterministic. AI/LLM calls are non-deterministic and must be isolated in activities:

```python
# ✅ Correct: LLM call in activity
@activity.defn
async def analyze_content(text: str) -> Analysis:
    llm = ChatAnthropic(...)
    return await llm.ainvoke(text)

# ❌ Wrong: LLM call in workflow
@workflow.defn
class MyWorkflow:
    async def run(self):
        llm = ChatAnthropic(...)  # Non-deterministic!
        result = await llm.ainvoke(...)  # Will break replay
```

### 2. Retry Policies for AI Services

LLM calls can fail due to rate limits, network issues, etc. Use retry policies:

```python
retry_policy = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=30),
    maximum_attempts=3,
    backoff_coefficient=2.0,
)

result = await workflow.execute_activity(
    ai_activity,
    args=[input_data],
    start_to_close_timeout=timedelta(seconds=120),
    retry_policy=retry_policy,
)
```

### 3. AI Agents with MCP Tools

Langchain agents can use MCP (Model Context Protocol) tools:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "tavily": {
        "transport": "streamable_http",
        "url": "https://mcp.tavily.com/..."
    }
})

tools = await client.get_tools(server_name="tavily")
agent = create_agent(llm, tools=tools)
```

### 4. Persistent Knowledge with MongoDB

Store research data for future reference:

```python
# Store sources during research
mongo_client.add_source({
    "title": "...",
    "url": "...",
    "key_facts": [...],
    "credibility_score": 0.85,
    "query_id": session_id,
})

# Retrieve related past research
past_sessions = mongo_client.get_past_research(query, limit=5)
```

### 5. Multi-Agent Patterns

**Supervision Pattern**: One supervisor coordinates specialized agents
**Swarm Pattern**: Multiple agents work independently and share findings

## Project Structure

```
langchain/
├── shared/                   # Shared utilities
│   ├── config/              # Configuration classes
│   └── utils/               # Helper functions
├── 1_llm_call/              # Project 1: Content Publishing
│   ├── activities/
│   │   ├── deterministic/   # Validation, image processing
│   │   └── llm_activities/  # Content analysis, SEO
│   ├── workflows/           # Main workflow
│   └── main.py              # Runner
├── 2_agents/                # Project 2: Research Assistant
│   ├── activities/
│   │   ├── deterministic/   # Query parsing
│   │   └── agent_activities/# Research agents
│   ├── agents/              # MongoDB client, MCP config
│   ├── workflows/           # Research workflow
│   └── main.py              # Runner
├── 3_multi-agents/          # Project 3: Code Review (Stub)
│   └── README.md
├── 4_all/                   # Project 4: Product Launch (Stub)
│   └── README.md
├── pyproject.toml           # Dependencies
├── .env.example             # Environment template
└── README.md                # This file
```

## Development Guidelines

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
```

### Type Checking

```bash
mypy .
```

## Common Patterns

### Activity Definition

```python
from temporalio import activity

@activity.defn
async def my_activity(input: str) -> str:
    activity.logger.info(f"Processing: {input}")
    # Your logic here
    return result
```

### Workflow Definition

```python
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, input: str) -> str:
        result = await workflow.execute_activity(
            my_activity,
            input,
            start_to_close_timeout=timedelta(seconds=30),
        )
        return result
```

### Worker Setup

```python
from temporalio.client import Client
from temporalio.worker import Worker

client = await Client.connect("localhost:7233")

worker = Worker(
    client,
    task_queue="my-queue",
    workflows=[MyWorkflow],
    activities=[my_activity],
)

await worker.run()
```

## Troubleshooting

### Temporal not running
```bash
docker ps  # Check if Temporal container is running
docker logs <container_id>  # Check logs
```

### MongoDB connection issues
```bash
docker ps  # Check if MongoDB is running
# Verify MONGODB_URI in .env
```

### Import errors
```bash
# Ensure virtual environment is activated
source .venv/bin/activate
# Reinstall dependencies
uv sync
```

### Activity timeouts
- Increase `start_to_close_timeout` for LLM activities
- Check API keys are valid
- Verify network connectivity

## Resources

- [Temporal Python SDK](https://docs.temporal.io/dev-guide/python)
- [Langchain Documentation](https://python.langchain.com/)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Temporal Samples](https://github.com/temporalio/samples-python)

## Next Steps

To complete Projects 3 and 4:

1. **Project 3**: Implement multi-agent supervision using LangGraph
2. **Project 4**: Combine all patterns in comprehensive workflow
3. **Add Tests**: Unit and integration tests for all activities
4. **Monitoring**: Add OpenTelemetry for observability
5. **Production**: Implement circuit breakers, rate limiting, cost tracking

## License

This project is for educational purposes demonstrating Temporal + Langchain integration.

## Contributing

This is a demonstration project. For your own implementations:
1. Follow SOLID principles
2. Implement comprehensive error handling
3. Add monitoring and observability
4. Secure API keys properly
5. Test thoroughly before production use

---

**Note**: Projects 3 and 4 are stub implementations showing architecture and planned features. Full implementation would follow the same patterns as Projects 1 and 2.
