# Claude Agent SDK + Temporal.io Integration

A comprehensive demonstration of integrating Claude Agent SDK within Temporal.io workflows, showcasing progressive complexity from simple LLM calls to sophisticated multi-agent orchestration.

## Overview

This repository contains four progressive projects that demonstrate different patterns of AI integration in workflow orchestration:

1. **Content Publishing Pipeline** - LLM calls within Temporal activities
2. **Research Assistant** - AI agents with persistent knowledge base (MongoDB)
3. **Code Review System** - Multi-agent teams with supervision pattern
4. **Product Launch Automation** - Combined approach using all patterns

## Project Structure

```
claude_agent_sdk/
├── shared/                     # Shared utilities and base classes
│   ├── config.py              # Configuration management
│   ├── sdk_wrapper.py         # Claude Agent SDK wrapper (simple_query, Agent, SupervisorTeam)
│   ├── mongodb_client.py      # MongoDB integration
│   └── models.py              # Pydantic data models
│
├── 1_llm_call/                # Project 1: Content Publishing
│   ├── activities.py          # Activity implementations (uses sdk_wrapper.simple_query)
│   ├── workflow.py            # Workflow definition
│   ├── worker.py              # Worker process
│   ├── starter.py             # Workflow starter
│   └── README.md              # Project documentation
│
├── 2_agents/                  # Project 2: Research Assistant
│   ├── agents.py              # AI agent implementations (uses sdk_wrapper.Agent)
│   ├── activities.py          # Activity implementations
│   ├── workflow.py            # Workflow definition
│   ├── worker.py              # Worker process
│   ├── starter.py             # Workflow starter
│   └── README.md              # Project documentation
│
├── 3_multi-agents/            # Project 3: Code Review
│   ├── agent_team_sdk.py      # Multi-agent team (uses sdk_wrapper.SupervisorTeam)
│   ├── activities.py          # Activity implementations
│   ├── workflow.py            # Workflow definition
│   ├── worker.py              # Worker process
│   ├── starter.py             # Workflow starter
│   └── README.md              # Project documentation
│
├── 4_all/                     # Project 4: Product Launch (Demo)
│   ├── workflow.py            # Workflow structure
│   ├── worker.py              # Worker process
│   ├── starter.py             # Workflow starter
│   └── README.md              # Project documentation
│
├── pyproject.toml             # Project dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── SDK_INTEGRATION_GUIDE.md  # Comprehensive SDK integration guide
├── SDK_QUICK_REFERENCE.md    # Quick reference for SDK patterns
└── README.md                  # This file
```

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Package Manager**: uv (recommended) or pip
- **Temporal Server**: Running instance
- **MongoDB**: Running instance (for Project 2)
- **OS**: Linux (Ubuntu), macOS, or WSL2

### External Services

- **Claude API**: Anthropic API key
- **MCP Services** (optional but recommended):
  - Tavily Search API key
  - E2B API key
  - Mem0 (OpenMemory) API key
  - ElevenLabs API key

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd claude_agent_sdk
```

### 2. Install Dependencies

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync

# Or using pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required configuration:

```env
# Temporal
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default

# MongoDB (Required for Project 2)
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/temporal_claude_sdk

# MCP Services (Optional)
TAVILY_API_KEY=your_tavily_key
E2B_API_KEY=your_e2b_key
OPENMEMORY_API_KEY=your_mem0_key
ELEVENLABS_API_KEY=your_elevenlabs_key
```

### 4. Start Temporal Server

#### Option A: Using Temporal CLI

```bash
temporal server start-dev
```

#### Option B: Using Docker

```bash
docker compose up -d
```

```yaml
# docker-compose.yml
version: "3.8"
services:
  temporal:
    image: temporalio/auto-setup:latest
    ports:
      - "7233:7233"
      - "8233:8233"
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=postgresql
```

### 5. Start MongoDB (for Project 2)

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install locally
# See: https://docs.mongodb.com/manual/installation/
```

## Quick Start

### Project 1: Content Publishing Pipeline

```bash
# Terminal 1: Start worker
uv run python -m 1_llm_call.worker

# Terminal 2: Execute workflow
uv run python -m 1_llm_call.starter
```

### Project 2: Research Assistant

```bash
# Terminal 1: Start worker
uv run python -m 2_agents.worker

# Terminal 2: Execute workflow
uv run python -m 2_agents.starter
```

### Project 3: Code Review

```bash
# Terminal 1: Start worker
uv run python -m 3_multi-agents.worker

# Terminal 2: Execute workflow
uv run python -m 3_multi-agents.starter
```

### Project 4: Product Launch (Demo)

```bash
# Terminal 1: Start worker
uv run python -m 4_all.worker

# Terminal 2: Execute workflow
uv run python -m 4_all.starter
```

## Project Descriptions

### Project 1: Content Publishing Pipeline

**Demonstrates**: LLM calls within Temporal activities

A content publishing workflow that processes articles through:

- Input validation (deterministic)
- Content analysis with LLM
- SEO optimization with LLM
- Image processing (deterministic)
- Final assembly and publishing (deterministic)

**Key Pattern**: Mixing deterministic and LLM-powered activities with retry logic

**Learn More**: See [1_llm_call/README.md](1_llm_call/README.md)

### Project 2: Research Assistant

**Demonstrates**: Individual AI agents with persistent storage

An automated research workflow featuring:

- Query parsing and session setup
- Web research agent (Tavily)
- Academic research agent (Academia)
- Data enrichment (deterministic)
- Knowledge graph builder agent
- Research synthesis agent (Mem0)
- Audio report generator (ElevenLabs)

**Key Pattern**: AI agents with MongoDB for persistent knowledge base

**Learn More**: See [2_agents/README.md](2_agents/README.md)

### Project 3: Code Review Pipeline

**Demonstrates**: Multi-agent teams with supervision pattern

A code review system with specialized agents:

- Supervisor Agent (coordinates team)
- Security Agent (vulnerability scanning)
- Performance Agent (complexity analysis)
- Style Agent (coding standards)
- Test Agent (test generation)

**Key Pattern**: Supervisor-worker multi-agent coordination

**Learn More**: See [3_multi-agents/README.md](3_multi-agents/README.md)

### Project 4: Product Launch Automation

**Demonstrates**: Combined approach (LLM + Agents + Multi-Agent Teams)

A comprehensive product launch workflow with:

- Launch planning (deterministic)
- Market research (swarm pattern)
- Content generation (LLM calls)
- Technical deployment (AI agent)
- Media asset creation (supervision pattern)
- Campaign orchestration (deterministic)
- Launch monitoring (AI agent + Mem0)
- Customer engagement (LLM calls)
- Post-launch analysis (multi-agent team)
- Archive and learn (deterministic + AI)

**Key Pattern**: Sophisticated orchestration of all AI integration patterns

**Learn More**: See [4_all/README.md](4_all/README.md)

## Architecture Patterns

### Pattern 1: LLM Calls in Activities

```python
@activity.defn
async def analyze_content(article: Article) -> Analysis:
    claude = ClaudeClient()
    response = await claude.simple_completion(
        prompt=f"Analyze this article: {article.content}",
        system="You are a content analyst..."
    )
    return parse_analysis(response)
```

**Use When**: Simple, stateless AI operations

### Pattern 2: Individual AI Agents

```python
class ResearchAgent:
    def __init__(self):
        self.claude = ClaudeClient()
        self.db = MongoDBClient()

    async def execute(self, query: str) -> Results:
        # Agent logic with state management
        results = await self.research(query)
        await self.db.store(results)
        return results
```

**Use When**: AI needs state, memory, or complex multi-step reasoning

### Pattern 3: Multi-Agent Teams

```python
class CodeReviewTeam:
    def __init__(self):
        self.supervisor = SupervisorAgent()
        self.security = SecurityAgent()
        self.performance = PerformanceAgent()

    async def review(self, code: Code) -> Report:
        # Parallel agent execution
        findings = await asyncio.gather(
            self.security.analyze(code),
            self.performance.analyze(code)
        )
        # Supervisor coordinates
        return await self.supervisor.coordinate(findings)
```

**Use When**: Complex tasks requiring specialized expertise and coordination

## Key Implementation Details

### Retry Logic

All AI activities use exponential backoff:

```python
ai_retry_policy = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    maximum_interval=timedelta(seconds=60),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)
```

### Error Handling

- **Validation errors**: Fail fast with clear messages
- **AI failures**: Automatic retry with backoff
- **Timeouts**: Activity-specific timeouts (30s-300s)
- **Graceful degradation**: Fallback to safe defaults when possible

### Monitoring

View workflows in Temporal UI:

```bash
# Open in browser
http://localhost:8233
```

Task queues:

- `content-publishing-queue`
- `research-assistant-queue`
- `code-review-queue`
- `product-launch-queue`

## Testing

### Unit Tests

```bash
pytest tests/unit/
```

### Integration Tests

```bash
# Requires Temporal and MongoDB running
pytest tests/integration/
```

### Replay Testing

Temporal's replay feature allows testing workflow changes:

```bash
temporal workflow replay --workflow-id <id>
```

## Development Workflow

1. **Start with deterministic skeleton**

   - Define workflow structure
   - Implement deterministic activities
   - Test basic orchestration

2. **Add LLM calls incrementally**

   - Identify activities needing AI
   - Implement with retry logic
   - Test error handling

3. **Introduce agents**

   - Create agent classes
   - Add state management
   - Implement agent activities

4. **Implement multi-agent coordination**

   - Design team structure
   - Implement coordination pattern
   - Test agent communication

5. **Add monitoring and observability**
   - Configure logging
   - Add metrics
   - Create dashboards

## Best Practices

### 1. Keep Activities Idempotent

```python
@activity.defn
async def process_data(data_id: str) -> Result:
    # Check if already processed
    if await is_processed(data_id):
        return await get_cached_result(data_id)

    # Process and cache
    result = await do_processing(data_id)
    await cache_result(data_id, result)
    return result
```

### 2. Use Proper Timeouts

```python
# Deterministic activities: short timeout
await workflow.execute_activity(
    validate_input,
    data,
    start_to_close_timeout=timedelta(seconds=30),
)

# AI activities: longer timeout
await workflow.execute_activity(
    ai_analysis,
    data,
    start_to_close_timeout=timedelta(seconds=180),
    retry_policy=ai_retry_policy,
)
```

### 3. Implement Circuit Breakers

```python
class ClaudeClient:
    def __init__(self):
        self.failure_count = 0
        self.circuit_open = False

    async def send_message(self, ...):
        if self.circuit_open:
            raise CircuitBreakerOpen()

        try:
            response = await self.client.messages.create(...)
            self.failure_count = 0
            return response
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= 5:
                self.circuit_open = True
            raise
```

### 4. Monitor Costs

```python
@activity.defn
async def track_ai_usage(activity_name: str, tokens: int, cost: float):
    await metrics.record(
        metric="ai_token_usage",
        value=tokens,
        tags={"activity": activity_name}
    )
    await metrics.record(
        metric="ai_cost",
        value=cost,
        tags={"activity": activity_name}
    )
```

## Troubleshooting

### Temporal Connection Issues

```bash
# Check Temporal is running
temporal workflow list

# Check namespace
temporal operator namespace list
```

### MongoDB Connection Issues

```bash
# Test MongoDB connection
mongosh mongodb://localhost:27017

# Check database
use temporal_claude_sdk
db.research_sources.find().limit(1)
```

### Worker Not Processing Tasks

1. Check task queue name matches
2. Verify workflow/activity registration
3. Check worker logs for errors
4. Ensure namespace is correct

## Performance Optimization

### 1. Parallel Activity Execution

```python
# Run independent activities in parallel
results = await asyncio.gather(
    workflow.execute_activity(activity1, ...),
    workflow.execute_activity(activity2, ...),
    workflow.execute_activity(activity3, ...),
)
```

### 2. Caching AI Responses

```python
# Cache similar prompts
cache_key = hashlib.md5(prompt.encode()).hexdigest()
if cached := await cache.get(cache_key):
    return cached

response = await claude.send_message(...)
await cache.set(cache_key, response, ttl=3600)
```

### 3. Batch Processing

```python
# Batch multiple items
@activity.defn
async def batch_analyze(items: List[Item]) -> List[Analysis]:
    # Process multiple items in one AI call
    combined_prompt = "\n\n".join(item.content for item in items)
    results = await claude.batch_analyze(combined_prompt)
    return results
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file

## Resources

### Documentation

- [Temporal Documentation](https://docs.temporal.io/)
- [Temporal Python SDK](https://docs.temporal.io/dev-guide/python)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Claude Agent SDK Examples](https://github.com/lukaskellerstein/ai/tree/main/14_Claude_Agent_SDK/claude_agent_sdk)
- [Temporal Samples](https://github.com/temporalio/samples-python)

### Related Projects

- [Temporal Core](https://github.com/temporalio/temporal)
- [Temporal Python SDK](https://github.com/temporalio/sdk-python)
- [Claude Code](https://claude.com/claude-code)
- [MCP Servers](https://modelcontextprotocol.io/)

## Support

- [GitHub Issues](https://github.com/your-repo/issues)
- [Temporal Community Forum](https://community.temporal.io/)
- [Anthropic Discord](https://discord.gg/anthropic)

## Acknowledgments

- Temporal team for excellent workflow orchestration
- Anthropic for Claude AI capabilities
- Open source community for MCP tools
- Contributors and reviewers

---

**Built with**:

- [Temporal.io](https://temporal.io/) - Workflow orchestration
- [Claude](https://anthropic.com/) - AI capabilities
- [Python](https://python.org/) - Implementation language
- [MongoDB](https://mongodb.com/) - Persistent storage
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
