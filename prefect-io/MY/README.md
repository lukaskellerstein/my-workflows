# Prefect Learning Examples

A comprehensive collection of Prefect workflow examples organized by complexity and use case.

## 📁 Project Structure

```
MY/
├── 0_simple/          # Basic workflow fundamentals
├── 1_basic/           # Child workflows and human interaction
├── 2_visualization/   # Workflow visualization
├── 2_advanced/        # Error handling and retry patterns
├── 3_concurrency/     # Parallel execution patterns
├── 4_human_in_loop/   # Advanced approval workflows
├── 5_AI/              # AI and LLM integration
├── 10_server/         # Server-based deployments & Docker Compose
├── pyproject.toml     # Project configuration & dependencies
├── Makefile           # Convenient command shortcuts
├── USAGE.md           # Quick reference guide for uv commands
└── README.md          # This file
```

## 🚀 Quick Start

### Prerequisites

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to the project
cd MY

# Create virtual environment and install dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

### Running Examples

Each folder contains standalone examples that can be run directly:

```bash
# Option 1: Run with activated venv
source .venv/bin/activate
python 0_simple/01_single_node.py

# Option 2: Run with uv directly (recommended)
uv run 0_simple/01_single_node.py
uv run 5_AI/01_llm_in_task.py
```

### AI Examples Setup

For AI examples, set your OpenAI API key:

```bash
export OPENAI_API_KEY='your-api-key-here'
```

### Full Usage Guide

For detailed uv commands and troubleshooting, see [USAGE.md](./USAGE.md)

## 📚 Learning Path

### Level 1: Fundamentals (0_simple)

Start here if you're new to Prefect.

1. **Single Node** - Simplest workflow with one task
2. **Multiple Nodes - Sequential** - Linear ETL pipeline
3. **Multiple Nodes - Fan-In/Fan-Out** - Parallel processing patterns
4. **IF Condition** - Conditional branching
5. **Loop** - Sequential and parallel loops

**Key Concepts**: `@flow`, `@task`, logging, task.map(), fan-out/fan-in

### Level 2: Composition & Interaction (1_basic)

Learn to build modular workflows and add human interaction.

1. **Child Workflows** - Compose workflows from reusable flows
2. **Human in the Loop** - Workflows requiring approval or input

**Key Concepts**: Flow composition, parent-child relationships, approval patterns

### Level 3: Visualization (2_visualization)

Learn to visualize and understand workflow execution.

1. **Basic Visualization** - Static diagrams with flow.visualize()
2. **UI Visualization** - Real-time execution graphs in Prefect UI

**Key Concepts**: flow.visualize(), Prefect UI, execution graphs, debugging

### Level 4: Resilience (2_advanced)

Build robust, fault-tolerant workflows.

1. **Retry Patterns** - Handle transient failures
   - Basic retry with fixed delay
   - Exponential backoff
   - Conditional retry
   - Retry with fallback

2. **Error Handling** - Graceful error management
   - Try-except patterns
   - Graceful degradation
   - State-based error handling
   - Custom error responses

**Key Concepts**: Retries, error handling, fault tolerance, fallback strategies

### Level 5: Performance (3_concurrency)

Optimize workflow execution with parallelism.

1. **Parallel Execution**
   - Sequential vs parallel comparison
   - Task mapping for parallelism
   - Thread pool task runners
   - Async/await patterns
   - Mixed parallel/sequential execution

**Key Concepts**: Concurrency, parallelism, task.map(), ThreadPoolTaskRunner, async

### Level 6: Advanced Human Integration (4_human_in_loop)

Build workflows that involve human decision-making.

1. **Human Approval**
   - Deployment approval workflow
   - Cost-based approval gates
   - Multi-stage approval process

**Key Concepts**: Approval patterns, workflow pauses, external integrations

### Level 7: AI Integration (5_AI)

Integrate AI and LLM capabilities into workflows.

1. **LLM in Task** - Direct LLM API calls
   - Simple LLM calls
   - Text extraction and classification
   - Document summarization
   - Conversational flows

2. **OpenAI Agent SDK** - Agentic workflows
   - Agents with custom tools
   - Multi-agent systems
   - Agent routing and specialization

3. **ReAct Agent** - Complete agent workflow
   - Thought → Action → Observation loop
   - Multi-step reasoning
   - Parallel agent execution

**Key Concepts**: LLM integration, agents, tools, ReAct pattern, agentic workflows

### Level 8: Server-Based Workflows (10_server)

Run workflows on a persistent Prefect server for production use.

1. **Docker Compose Setup** - Run Prefect server locally
   - PostgreSQL backend
   - Persistent data storage
   - Production-like environment

2. **Deployments** - Deploy flows to server
   - Simple deployments with `serve()`
   - Scheduled workflows (cron, interval)
   - Parameterized deployments
   - API-triggered flows

3. **Work Pools & Workers** - Scalable execution
   - Separate deployment from execution
   - Scale workers independently
   - Production architecture patterns

**Key Concepts**: Deployments, serve(), deploy(), work pools, workers, scheduling, API integration

## 🎯 Use Case Index

### By Use Case

**Data Engineering**
- ETL Pipeline: `0_simple/02_multiple_nodes.py`
- Fan-In/Fan-Out: `0_simple/03_fan_in_fan_out.py`
- Parallel Processing: `3_concurrency/01_parallel_execution.py`
- Data Validation: `0_simple/04_if_condition.py`

**DevOps & Deployment**
- Deployment Pipeline: `1_basic/02_human_in_loop.py`
- Advanced Approval: `4_human_in_loop/01_human_approval.py`
- Multi-Stage Deployment: `4_human_in_loop/01_human_approval.py`

**AI & Machine Learning**
- LLM Integration: `5_AI/01_llm_in_task.py`
- AI Agents: `5_AI/02_openai_agent.py`
- ReAct Agents: `5_AI/03_react_agent_workflow.py`

**Error Handling & Resilience**
- API Retry Patterns: `2_advanced/01_retry_patterns.py`
- Fault Tolerance: `2_advanced/02_error_handling.py`

**Batch Processing**
- Sequential Batches: `0_simple/05_loop.py`
- Parallel Batches: `0_simple/05_loop.py`
- Distributed Processing: `0_simple/03_fan_in_fan_out.py`
- Large Scale Processing: `3_concurrency/01_parallel_execution.py`

**Visualization & Debugging**
- Static Diagrams: `2_visualization/01_basic_visualization.py`
- UI Visualization: `2_visualization/02_ui_visualization.py`

**Server & Production Deployments**
- Docker Compose Setup: `10_server/docker-compose.yml`
- Simple Deployment: `10_server/01_simple_deployment.py`
- Scheduled Workflows: `10_server/02_scheduled_deployment.py`
- Parameterized Flows: `10_server/03_parameterized_deployment.py`
- API Triggers: `10_server/04_trigger_via_api.py`
- Work Pools: `10_server/05_work_pool.py`

## 🔑 Key Prefect Concepts

### Flows
The orchestration layer. Decorated with `@flow`, flows coordinate tasks and other flows.

```python
@flow(name="My Flow", log_prints=True)
def my_flow():
    result = my_task()
    return result
```

### Tasks
Units of work. Decorated with `@task`, tasks are the building blocks.

```python
@task(retries=3, retry_delay_seconds=2)
def my_task():
    return "result"
```

### Task Mapping
Parallel execution across multiple inputs.

```python
results = my_task.map([1, 2, 3, 4, 5])
```

### Retries
Automatic retry on failure.

```python
@task(retries=3, retry_delay_seconds=[1, 2, 5])
def unreliable_task():
    pass
```

### Logging
Built-in logging for observability.

```python
from prefect import get_run_logger

@task
def my_task():
    logger = get_run_logger()
    logger.info("Task running")
```

## 📊 Performance Comparison

| Pattern | 5 Tasks (0.5s each) | Speedup |
|---------|-------------------|---------|
| Sequential | ~2.5 seconds | 1x |
| Parallel (map) | ~0.5 seconds | 5x |
| Thread Pool | ~0.5 seconds | 5x |
| Async | ~0.5 seconds | 5x |

## 🛠️ Development Tips

### Running with Prefect UI

```bash
# Start Prefect server (optional)
prefect server start

# Run a flow
python 0_simple/01_single_node.py

# View in UI at http://localhost:4200
```

### Debugging

```python
@flow(log_prints=True)  # Print statements appear in logs
def debug_flow():
    print("Debug info")  # Will be logged

    logger = get_run_logger()
    logger.info("Structured log")
```

### Testing

```python
# Test flows like regular Python functions
def test_my_flow():
    result = my_flow(test_input)
    assert result == expected_output
```

## 📖 Additional Resources

- **Prefect Documentation**: https://docs.prefect.io/v3/concepts
- **Source Code**: `../prefect/`
- **More Examples**: `../examples/`

## 🎓 Learning Checklist

- [ ] Run all examples in `0_simple/`
- [ ] Understand sequential vs fan-in/fan-out patterns
- [ ] Master parent-child workflows in `1_basic/`
- [ ] Add human approval to a workflow
- [ ] Visualize workflows with both methods
- [ ] Implement retry strategy in your own workflow
- [ ] Create a parallel processing workflow
- [ ] Integrate an LLM into a workflow
- [ ] Build a custom ReAct agent
- [ ] Deploy flow to Prefect server with Docker Compose
- [ ] Create scheduled deployment
- [ ] Trigger flows via API

## 💡 Next Steps

After completing these examples:

1. **Server Deployments**: Start with `10_server/` for production patterns
2. **Build Your Own**: Apply patterns to your use case
3. **Production Setup**: Configure Prefect Cloud or self-hosted server
4. **Advanced Features**: Blocks, automations, webhooks
5. **Integrations**: Explore Prefect's integration ecosystem
6. **CI/CD**: Automate deployment pipelines
7. **Kubernetes**: Deploy to K8s for enterprise scale

## 🤝 Contributing

Found an issue or want to add an example? Feel free to contribute!

## 📝 Notes

- All examples are self-contained and runnable
- AI examples require OpenAI API key
- Server examples require Docker and Docker Compose
- Examples use simulated data for demonstration
- Patterns are production-ready but may need adaptation

---

**Happy Learning! 🎉**

Start with `0_simple/` and work your way up to `10_server/` for production deployments!
