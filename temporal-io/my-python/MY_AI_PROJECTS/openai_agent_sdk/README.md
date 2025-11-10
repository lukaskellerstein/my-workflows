# OpenAI Agent SDK + Temporal.io Integration

This repository demonstrates four progressive projects showcasing the integration of the **OpenAI Agent SDK** within **Temporal.io workflows**, illustrating how to build production-grade AI-powered automation systems with durability, observability, and resilience.

## 🎯 Project Overview

| Project | Focus | Key Technologies | Complexity |
|---------|-------|------------------|------------|
| **[1. Content Publishing Pipeline](1_llm_call/)** | LLM Calls in Workflows | OpenAI GPT-5-mini, Basic Agents | ⭐ Beginner |
| **[2. Research Assistant](2_agents/)** | AI Agents + MCP Tools + MongoDB | Tavily, Academia, Mem0, ElevenLabs, MongoDB | ⭐⭐⭐ Intermediate |
| **[3. Code Review Pipeline](3_multi-agents/)** | Multi-Agent Teams (Supervision) | E2B Sandbox, Agent Coordination | ⭐⭐⭐⭐ Advanced |
| **[4. Product Launch Automation](4_all/)** | All Patterns Combined | Complete Integration | ⭐⭐⭐⭐⭐ Expert |

## 🏗️ Architecture Patterns

### Pattern 1: LLM Calls (Project 1)
Simple AI enhancements within deterministic workflows.

```python
@workflow.defn
class ContentWorkflow:
    async def run(self, article):
        # Deterministic validation
        validation = await workflow.execute_activity(validate, article)

        # LLM-powered analysis
        analysis = await workflow.execute_activity(llm_analyze, article)

        # Deterministic assembly
        result = await workflow.execute_activity(assemble, validation, analysis)
        return result
```

**Use Cases**: Content generation, text analysis, SEO optimization

---

### Pattern 2: AI Agents with MCP Tools (Project 2)
Specialized agents equipped with external tools via Model Context Protocol.

```python
@activity.defn
async def research_web_sources(query):
    with trace(workflow_name="Web Research"):
        # Agent with Tavily MCP for web search
        agent = Agent(
            name="Web Researcher",
            mcp_servers=[tavily_server],
        )
        result = await Runner.run(agent, input=query)
        return result
```

**Use Cases**: Research automation, data gathering, knowledge synthesis

---

### Pattern 3: Multi-Agent Teams - Supervision (Project 3)
A supervisor agent coordinates multiple specialist agents.

```python
@workflow.defn
class CodeReviewWorkflow:
    async def run(self, code):
        # Supervisor coordinates specialists
        supervisor = Agent(name="Review Coordinator")

        # Parallel execution of specialists
        security, perf, style = await workflow.wait_all([
            workflow.execute_activity(security_agent, code),
            workflow.execute_activity(perf_agent, code),
            workflow.execute_activity(style_agent, code),
        ])

        # Supervisor aggregates findings
        report = await supervisor.aggregate([security, perf, style])
        return report
```

**Use Cases**: Code review, quality assurance, multi-perspective analysis

---

### Pattern 4: Multi-Agent Teams - Swarm (Project 4)
Agents collaborate with shared state, enabling emergent insights.

```python
swarm = AgentSwarm(
    agents=[analyst1, analyst2, analyst3],
    shared_memory=True,
)
insights = await swarm.execute(market_research_task)
```

**Use Cases**: Market research, brainstorming, complex problem-solving

---

## 📦 Project Summaries

### Project 1: Content Publishing Pipeline
**Goal**: Demonstrate LLM calls mixed with deterministic activities

**Workflow**: Article → Validation → Analysis (LLM) → SEO (LLM) → Images → Publication

**Key Learning**:
- Mixing deterministic and AI activities
- Retry policies for LLM calls
- Error handling and graceful degradation

[→ Full Documentation](1_llm_call/README.md)

---

### Project 2: Research Assistant with Knowledge Base
**Goal**: AI agents with MCP tools + persistent MongoDB storage

**Workflow**: Query → Context (MongoDB) → Web Research (Tavily) → Academic Research (Academia) → Knowledge Graph → Synthesis (Mem0) → Audio (ElevenLabs) → Storage (MongoDB)

**Key Learning**:
- MCP integration with agents
- MongoDB for persistent knowledge
- Parallel agent execution
- Knowledge graph construction

[→ Full Documentation](2_agents/README.md)

---

### Project 3: Code Review Pipeline
**Goal**: Multi-agent teams using supervision pattern

**Workflow**: Code → Supervisor → [Security Agent, Performance Agent, Style Agent, Test Agent] → Aggregation → Report

**Key Learning**:
- Supervisor-worker pattern
- Agent specialization
- Result aggregation
- Conflict resolution

[→ Full Documentation](3_multi-agents/README.md)

---

### Project 4: Product Launch Automation
**Goal**: Complete integration of all patterns

**Workflow**: 9 phases combining deterministic steps, LLM calls, single agents, and multi-agent teams (both supervision and swarm patterns)

**Key Learning**:
- Pattern composition
- Dynamic workflow adaptation
- Human-in-the-loop
- Production readiness

[→ Full Documentation](4_all/README.md)

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+** with `uv` package manager
2. **Temporal Server**
   ```bash
   temporal server start-dev
   ```
3. **MongoDB** (for Project 2)
   ```bash
   # With authentication (recommended)
   docker run -d -p 27017:27017 \
     -e MONGO_INITDB_ROOT_USERNAME=admin \
     -e MONGO_INITDB_ROOT_PASSWORD=admin123 \
     mongo:latest
   ```
   See [MONGODB_SETUP.md](MONGODB_SETUP.md) for detailed setup and troubleshooting

4. **Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   # MongoDB URI: mongodb://admin:admin123@localhost:27017/
   ```

### Installation

```bash
# Clone repository
cd openai_agent_sdk

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv sync
```

### Run a Project

```bash
# Terminal 1: Start worker
python 1_llm_call/run_worker.py

# Terminal 2: Execute workflow
python 1_llm_call/run_workflow.py
```

---

## 📚 Key Concepts

### Why Temporal + OpenAI Agents?

| Temporal Benefits | OpenAI Agents Benefits | Combined Power |
|-------------------|------------------------|----------------|
| Durable execution | AI capabilities | Reliable AI workflows |
| Automatic retries | Tool integration (MCP) | Resilient AI operations |
| State persistence | Agent collaboration | Long-running AI tasks |
| Observability | Context management | Debuggable AI systems |
| Versioning | Structured outputs | Evolvable AI workflows |

### MCP (Model Context Protocol) Integration

MCP servers provide specialized capabilities to agents:

- **Tavily**: Web search and analysis
- **Academia**: Academic paper search
- **E2B**: Code execution sandbox
- **Mem0**: Long-term memory
- **ElevenLabs**: Text-to-speech
- **MongoDB**: Data persistence

### Agent Coordination Patterns

1. **Sequential**: One agent after another
2. **Parallel**: Multiple agents simultaneously
3. **Supervision**: Coordinator + specialists
4. **Swarm**: Collaborative with shared state

---

## 🏛️ Project Structure

```
openai_agent_sdk/
├── 1_llm_call/                 # Project 1: LLM Calls
│   ├── models/                 # Data models
│   ├── activities/             # Deterministic + LLM activities
│   ├── workflows/              # Workflow definition
│   ├── run_worker.py           # Worker script
│   ├── run_workflow.py         # Client script
│   └── README.md               # Project documentation
│
├── 2_agents/                   # Project 2: AI Agents + MCP + MongoDB
│   ├── models/                 # Data models
│   ├── activities/             # MongoDB + Agent activities
│   ├── workflows/              # Workflow definition
│   ├── mcp_configs/            # MCP server configs
│   ├── run_worker.py
│   ├── run_workflow.py
│   └── README.md
│
├── 3_multi-agents/             # Project 3: Multi-Agent Teams
│   ├── models/
│   ├── activities/
│   ├── workflows/
│   ├── run_worker.py
│   ├── run_workflow.py
│   └── README.md
│
├── 4_all/                      # Project 4: Complete Integration
│   ├── models/
│   ├── activities/
│   ├── workflows/
│   ├── run_worker.py
│   ├── run_workflow.py
│   └── README.md
│
├── pyproject.toml              # Dependencies
├── .env.example                # Environment template
├── .gitignore
└── README.md                   # This file
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Temporal
TEMPORAL_ADDRESS=localhost:7233
TEMPORAL_NAMESPACE=default

# MongoDB (Project 2)
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=research_assistant

# MCP Tools
TAVILY_API_KEY=tvly-...
E2B_API_KEY=e2b_...
MEM0_API_KEY=om-...
ELEVENLABS_API_KEY=sk_...
```

### Dependencies

Managed via `pyproject.toml`:

```toml
[project.dependencies]
temporalio[openai-agents] = ">=1.18.0"
openai-agents[litellm] = "==0.3.2"
pymongo = ">=4.10.0"
fastapi = ">=0.115.0"
uvicorn = ">=0.32.0"
python-dotenv = ">=1.0.0"
```

---

## 🎓 Learning Path

### Beginner
1. Start with **Project 1** to understand basic LLM integration
2. Learn about activity retries and error handling
3. Understand deterministic vs non-deterministic activities

### Intermediate
1. Move to **Project 2** for AI agents with MCP tools
2. Learn MongoDB integration patterns
3. Understand parallel agent execution
4. Explore knowledge graph construction

### Advanced
1. Study **Project 3** for multi-agent coordination
2. Learn supervision pattern
3. Understand agent specialization
4. Master result aggregation

### Expert
1. Explore **Project 4** for complete integration
2. Learn pattern composition
3. Understand dynamic workflow adaptation
4. Build production-ready systems

---

## 🧪 Testing

Each project includes:

```bash
# Run project tests
pytest 1_llm_call/tests/

# Test with mock LLM responses
pytest --mock-llm

# Integration tests
pytest --integration
```

---

## 📊 Monitoring

### Temporal Web UI
- Navigate to `http://localhost:8233`
- View workflow execution timeline
- Inspect activity inputs/outputs
- Debug failures with complete history

### MongoDB (Project 2)
```bash
mongosh
use research_assistant
db.research_sources.find().pretty()
db.knowledge_graph.find()
```

### Metrics
- Token usage per activity
- Agent execution time
- Cost tracking
- Success rates

---

## 🛡️ Best Practices

### Error Handling
```python
# Retry policy for LLM activities
retry_policy = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=30),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)

result = await workflow.execute_activity(
    llm_activity,
    retry_policy=retry_policy,
)
```

### Cost Management
```python
# Track tokens and costs
@activity.defn
async def llm_activity(input):
    result = await runner.run(agent, input)
    activity.heartbeat({"tokens": result.usage.total_tokens})
    return result
```

### Security
- Sanitize all inputs before LLM calls
- Validate agent outputs
- Use environment variables for secrets
- Implement rate limiting

---

## 🤝 Contributing

Contributions welcome! Focus areas:
- Additional MCP server integrations
- New agent coordination patterns
- Performance optimizations
- Documentation improvements

---

## 📖 Resources

### Documentation
- [Temporal.io Docs](https://docs.temporal.io/)
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- [Model Context Protocol](https://modelcontextprotocol.io/)

### Related Projects
- [Temporal Python SDK](https://github.com/temporalio/sdk-python)
- [Temporal Samples](https://github.com/temporalio/samples-python)

---

## 📝 License

MIT License - See LICENSE file

---

## 🎉 Summary

This repository provides a comprehensive guide to building production-grade AI-powered automation systems by combining:

✅ **Temporal.io** - Durable workflow execution
✅ **OpenAI Agents SDK** - AI capabilities
✅ **MCP Tools** - Specialized integrations
✅ **MongoDB** - Persistent knowledge
✅ **Multi-Agent Patterns** - Complex coordination

Start with Project 1 and progress through increasing complexity to master AI workflow orchestration!

---

**Questions?** Open an issue or refer to individual project READMEs for detailed documentation.
