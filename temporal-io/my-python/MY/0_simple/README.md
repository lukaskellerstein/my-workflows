# 0_simple - Basic Temporal Workflow Examples

This folder contains simple examples demonstrating fundamental Temporal workflow patterns.

## Prerequisites

1. **Start Temporal Server** (if not already running):
   ```bash
   temporal server start-dev
   ```

2. **Install Python dependencies**:
   ```bash
   cd /path/to/temporalio
   # If using uv:
   uv venv
   source .venv/bin/activate
   uv sync
   ```

## Examples

### 1. Single Node Workflow (`single_node.py`)

The simplest possible workflow with a single activity.

**Demonstrates:**
- Basic workflow structure
- Single activity execution
- Activity logging

**Run:**
```bash
python MY/0_simple/single_node.py
```

### 2. Multiple Nodes Workflow - Sequential (`multiple_nodes.py`)

A workflow with multiple activities executed sequentially.

**Demonstrates:**
- Sequential activity execution
- Data flow between activities
- Basic validation pattern

**Run:**
```bash
python MY/0_simple/multiple_nodes.py
```

### 3. Multiple Nodes Workflow - Fan-In/Fan-Out (`fan_in_fan_out.py`)

A workflow that executes multiple activities in parallel and aggregates results.

**Demonstrates:**
- Parallel activity execution (Fan-Out)
- Result aggregation (Fan-In)
- Using `asyncio.gather` for parallelism
- Batch processing optimization

**Key Pattern:**
- **Fan-Out**: Split work into parallel tasks
- **Fan-In**: Collect and aggregate results

**Run:**
```bash
python MY/0_simple/fan_in_fan_out.py
```

**Use Cases:**
- Parallel data processing
- Concurrent API calls
- Distributed computations
- Performance optimization

### 4. Workflow with IF Condition (`if_condition.py`)

Demonstrates conditional workflow execution based on runtime data.

**Demonstrates:**
- Conditional branching
- Different execution paths
- Priority-based processing

**Run:**
```bash
python MY/0_simple/if_condition.py
```

### 5. Workflow with LOOP (`loop.py`)

A workflow that processes multiple items in a loop.

**Demonstrates:**
- Iterating over collections
- Batch processing pattern
- Result aggregation

**Run:**
```bash
python MY/0_simple/loop.py
```

## Key Concepts

### Workflow
- Defined with `@workflow.defn` decorator
- Contains the business logic and orchestration
- `@workflow.run` method is the entry point

### Activity
- Defined with `@activity.defn` decorator
- Contains the actual work (e.g., API calls, database operations)
- Can fail and be retried automatically

### Worker
- Executes workflows and activities
- Connects to Temporal server
- Configured with task queue name

### Client
- Starts workflow executions
- Queries workflow state
- Sends signals to workflows

## Common Patterns

1. **Error Handling**: Activities can fail and be retried automatically
2. **Durability**: Workflows survive process restarts
3. **Timeouts**: Activities have configurable timeouts
4. **Logging**: Use `workflow.logger` and `activity.logger`

## Next Steps

After understanding these basic patterns, check out:
- `1_basic/` - Child workflows
- `5_AI/` - AI integration examples
