# 0_simple - Basic Prefect Workflow Examples

This folder contains fundamental Prefect workflow examples to help you get started.

## Examples

### 1. Single Node Workflow (`01_single_node.py`)
The simplest possible workflow with a single task.

**Demonstrates:**
- Basic `@flow` and `@task` decorators
- Logging with `get_run_logger()`
- Running flows with different parameters

**Run:**
```bash
python 01_single_node.py
```

### 2. Multiple Nodes Workflow - Sequential (`02_multiple_nodes.py`)
A classic ETL (Extract, Transform, Load) pipeline with multiple tasks in sequence.

**Demonstrates:**
- Sequential task execution (one after another)
- Data passing between tasks
- ETL pattern implementation
- Linear data flow

**Run:**
```bash
python 02_multiple_nodes.py
```

### 3. Multiple Nodes Workflow - Fan-In/Fan-Out (`03_fan_in_fan_out.py`)
Demonstrates the fan-in/fan-out pattern for parallel processing.

**Demonstrates:**
- **Fan-Out**: Splitting work into parallel branches
- **Parallel Processing**: Multiple tasks running concurrently
- **Fan-In**: Combining results from parallel branches
- Multi-stage fan-in/fan-out pipelines
- Distributed batch processing

**Key Pattern:**
```
        ┌─> Task 1 ─┐
Source ─┼─> Task 2 ─┼─> Aggregate
        └─> Task 3 ─┘
```

**Run:**
```bash
python 03_fan_in_fan_out.py
```

### 4. Workflow with IF Condition (`04_if_condition.py`)
Conditional branching based on data quality checks.

**Demonstrates:**
- Conditional logic in flows
- Branching execution paths
- Data validation patterns

**Run:**
```bash
python 04_if_condition.py
```

### 5. Workflow with LOOP (`05_loop.py`)
Multiple loop patterns including sequential, parallel, and nested loops.

**Demonstrates:**
- Sequential loops for ordered processing
- Parallel execution using `task.map()`
- Nested loops for hierarchical data
- Performance comparison between sequential and parallel

**Run:**
```bash
python 05_loop.py
```

## Key Concepts

- **Flow**: An orchestrator function decorated with `@flow` that defines the workflow
- **Task**: A unit of work decorated with `@task` that can be retried, cached, and monitored
- **Task Mapping**: Using `.map()` to execute a task in parallel across multiple inputs
- **Logging**: Built-in logging with `get_run_logger()` for observability

## Next Steps

After mastering these basics, check out:
- `../1_basic/` - Child/nested workflows
- `../5_AI/` - AI integration examples
