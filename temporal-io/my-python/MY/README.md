# Temporal Learning Examples

A comprehensive collection of examples demonstrating Temporal workflow capabilities, from basic patterns to advanced AI integration.

> **Quick Setup**: See [SETUP.md](SETUP.md) for detailed installation and setup instructions.

## 📚 Learning Path

This repository is organized into progressive learning modules:

```
0_simple/         → Basic workflow patterns
1_basic/          → Child workflows and human-in-the-loop
2_visualization/  → Workflow visualization and monitoring
5_AI/             → AI/LLM integration
```

### Recommended Learning Order

1. **Start Here:** `0_simple/` - Understand core workflow concepts
2. **Next:** `1_basic/` - Learn about workflow composition and approvals
3. **Then:** `2_visualization/` - Monitor and visualize workflows
4. **Finally:** `5_AI/` - Integrate AI capabilities

## 📖 Quick Start

### Prerequisites

1. **Install Temporal CLI and start server:**
   ```bash
   temporal server start-dev
   ```

2. **Set up Python environment (from the MY folder):**
   ```bash
   cd MY

   # Install dependencies
   uv sync

   # For AI examples, also install AI dependencies
   uv sync --extra ai
   ```

3. **For AI examples, set OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

### Run Examples

**Option 1: Interactive Launcher (Recommended)**
```bash
uv run python main.py
```

**Option 2: Run Examples Directly**
```bash
# Run any example directly
uv run python 0_simple/single_node.py
uv run python 1_basic/child_workflow.py
uv run python 5_AI/simple_llm_call.py
```

**Option 3: Activate virtual environment**
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python 0_simple/single_node.py
```

## 📂 Folder Structure

### 0_simple - Basic Patterns

**Learn:** Fundamental workflow building blocks

**Examples:**
- `single_node.py` - Simplest workflow with one activity
- `multiple_nodes.py` - Sequential activity execution
- `fan_in_fan_out.py` - Parallel execution with fan-out/fan-in pattern
- `if_condition.py` - Conditional branching
- `loop.py` - Iterating over collections

**Key Concepts:**
- Workflows and activities
- Data flow
- Sequential and parallel execution
- Basic control flow
- Error handling

**Time:** 40 minutes

---

### 1_basic - Child Workflows and Human-in-the-Loop

**Learn:** Workflow composition and human approval patterns

**Examples:**
- `child_workflow.py` - E-commerce order processing with child workflows
- `human_in_loop.py` - Expense approval workflow with human decisions

**Key Concepts:**
- Parent-child workflow relationships
- Workflow reusability
- Signals and queries
- Human approval patterns
- Timeout handling

**Use Cases:**
- Order processing
- Expense approvals
- Document review
- Data pipelines
- Access requests

**Time:** 35 minutes

---

### 2_visualization - Workflow Visualization and Monitoring

**Learn:** How to visualize and monitor workflow execution

**Examples:**
- `workflow_history_viewer.py` - Retrieve and visualize workflow history
- `workflow_state_monitor.py` - Real-time workflow state monitoring

**Key Concepts:**
- Workflow history API
- Event timeline visualization
- Query-based monitoring
- Progress tracking
- Real-time state inspection

**Use Cases:**
- Debugging workflows
- Building dashboards
- Performance analysis
- Operational monitoring
- Custom reporting

**Time:** 30 minutes

---

### 5_AI - AI Integration

**Learn:** Integrating LLMs and AI agents with workflows

**Examples:**
- `simple_llm_call.py` - Basic LLM API calls
- `ai_agent_with_tools.py` - OpenAI Agent SDK with tools
- `react_agent.py` - Complete ReAct agent implementation

**Key Concepts:**
- LLM integration patterns
- AI agent orchestration
- Tool calling
- ReAct (Reasoning + Acting)
- Multi-step reasoning

**Use Cases:**
- Intelligent assistants
- Content analysis
- Research automation
- Decision support
- Customer service

**Time:** 60 minutes

**Note:** Requires OpenAI API key

## 🎯 Learning Objectives

By the end of these examples, you will understand:

### Core Concepts
- ✅ How to define workflows and activities
- ✅ Data flow between workflow components
- ✅ Control flow (conditions, loops)
- ✅ Error handling and retries

### Composition
- ✅ Breaking down complex workflows
- ✅ Using child workflows
- ✅ Aggregating results

### Interaction
- ✅ Sending signals to workflows
- ✅ Querying workflow state
- ✅ Implementing approval patterns
- ✅ Human-in-the-loop workflows

### AI Integration
- ✅ Calling LLMs from workflows
- ✅ Building AI agents with tools
- ✅ Implementing ReAct patterns
- ✅ Multi-step AI reasoning

## 🔑 Key Temporal Concepts

### Workflow
```python
@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, input: str) -> str:
        # Orchestration logic
        return result
```
- Orchestrates business logic
- Durable and resumable
- Survives process failures

### Activity
```python
@activity.defn
async def my_activity(input: str) -> str:
    # Actual work (API calls, DB operations)
    return result
```
- Performs actual work
- Can fail and retry
- Has timeouts and retry policies

### Signal
```python
@workflow.signal
async def my_signal(self, data: str) -> None:
    self._state = data
```
- One-way message to workflow
- Updates workflow state
- Asynchronous

### Query
```python
@workflow.query
def my_query(self) -> str:
    return self._state
```
- Read workflow state
- Synchronous
- No side effects

## 🛠️ Common Patterns

### Pattern: Sequential Processing
```
Activity A → Activity B → Activity C
```
**Use:** Step-by-step data transformation

### Pattern: Parallel Execution
```python
results = await asyncio.gather(
    workflow.execute_activity(activity1, ...),
    workflow.execute_activity(activity2, ...),
)
```
**Use:** Independent concurrent operations

### Pattern: Conditional Branching
```python
if condition:
    result = await workflow.execute_activity(activity_a, ...)
else:
    result = await workflow.execute_activity(activity_b, ...)
```
**Use:** Different paths based on data

### Pattern: Loop Processing
```python
for item in items:
    result = await workflow.execute_activity(process_item, item)
```
**Use:** Batch processing

### Pattern: Parent-Child
```python
result = await workflow.execute_child_workflow(
    ChildWorkflow.run, input
)
```
**Use:** Modular workflow composition

### Pattern: Human-in-the-Loop
```python
await notify_human()
await workflow.wait_condition(
    lambda: self._decision_made,
    timeout=timedelta(hours=24)
)
```
**Use:** Approval and decision workflows

### Pattern: AI Agent
```python
agent = Agent(
    name="Assistant",
    tools=[activity_as_tool(my_activity)]
)
result = await Runner.run(agent, input=prompt)
```
**Use:** Intelligent automation

## 🚀 Real-World Use Cases

### E-commerce
- Order processing (`1_basic/child_workflow.py`)
- Shopping cart management (`2_intermediate/signal_and_query.py`)
- Inventory management
- Payment processing

### Human Resources
- Expense approval (`2_intermediate/human_in_loop.py`)
- Leave requests
- Onboarding workflows
- Performance reviews

### Content Management
- Document approval workflows
- Content moderation with AI (`5_AI/simple_llm_call.py`)
- Publishing pipelines

### Customer Service
- AI-powered support agents (`5_AI/ai_agent_with_tools.py`)
- Ticket routing
- Escalation workflows

### Data Processing
- ETL pipelines
- Batch processing (`0_simple/loop.py`)
- Data validation
- Report generation

## 📊 Comparison with Other Systems

| Feature | Temporal | Traditional Queue | State Machine |
|---------|----------|-------------------|---------------|
| Durability | ✅ Built-in | ⚠️ Depends | ❌ Usually not |
| State Management | ✅ Automatic | ❌ Manual | ✅ Yes |
| Versioning | ✅ Built-in | ❌ No | ⚠️ Complex |
| Visibility | ✅ Full history | ⚠️ Limited | ⚠️ Current state |
| Complex Logic | ✅ Easy | ❌ Difficult | ⚠️ Moderate |
| Human Input | ✅ Natural | ❌ Awkward | ⚠️ Possible |

## 🔍 Debugging Tips

### 1. Use Temporal Web UI
```bash
# Access at http://localhost:8233
temporal server start-dev
```

### 2. Enable Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### 3. Query Workflow State
```python
status = await handle.query(MyWorkflow.get_status)
print(f"Current status: {status}")
```

### 4. Check Workflow History
Use Temporal Web UI to see all workflow events

## 💡 Best Practices

### ✅ Do
- Keep activities idempotent
- Use meaningful workflow and activity names
- Set appropriate timeouts
- Use signals for external events
- Use queries for state inspection
- Handle errors gracefully
- Test with mock responses

### ❌ Don't
- Don't make workflows non-deterministic
- Don't use random() or time.now() in workflows
- Don't perform I/O in workflows (use activities)
- Don't modify workflow state in queries
- Don't forget timeout configurations
- Don't ignore error handling

## 📚 Additional Resources

### Official Documentation
- [Temporal Documentation](https://docs.temporal.io/)
- [Python SDK Guide](https://docs.temporal.io/develop/python/)
- [Temporal Concepts](https://docs.temporal.io/concepts/)

### Sample Code
- `../samples-python/` - Official Temporal samples
- [Temporal Samples Repository](https://github.com/temporalio/samples-python)

### Learning Materials
- [Temporal 101 Course](https://learn.temporal.io/)
- [Temporal YouTube Channel](https://www.youtube.com/c/Temporal-oss)

### Community
- [Temporal Slack](https://temporal.io/slack)
- [Temporal Community Forum](https://community.temporal.io/)

## 🤝 Contributing

Found an issue or want to improve an example?
- Check existing samples for patterns
- Follow the established code style
- Add comprehensive comments
- Update README files

## 📝 License

These examples are part of the Temporal samples repository and follow the same license.

## 🎓 What's Next?

After completing these examples:

1. **Explore Official Samples:** Check `../samples-python/` for more advanced patterns
2. **Build a Project:** Apply what you learned to a real use case
3. **Read the Docs:** Deep dive into [Temporal documentation](https://docs.temporal.io/)
4. **Join the Community:** Get help on [Temporal Slack](https://temporal.io/slack)

## 📞 Getting Help

- **Examples Issues:** Check README in each folder
- **Temporal Issues:** [GitHub Issues](https://github.com/temporalio/sdk-python/issues)
- **Questions:** [Temporal Community Forum](https://community.temporal.io/)
- **Real-time Help:** [Temporal Slack](https://temporal.io/slack)

---

**Happy Learning! 🚀**

Start with `0_simple/single_node.py` and work your way up!
