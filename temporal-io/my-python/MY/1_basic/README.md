# 1_basic - Basic Workflow Patterns

This folder demonstrates basic workflow patterns including child workflows and human-in-the-loop approval workflows.

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

### 1. Child Workflow (`child_workflow.py`)

#### Overview

The `child_workflow.py` example demonstrates a practical e-commerce order processing scenario:

- **Parent Workflow**: `ProcessOrderWorkflow` - Orchestrates the entire order process
- **Child Workflow**: `ProcessOrderItemWorkflow` - Processes individual order items

### Architecture

```
ProcessOrderWorkflow (Parent)
├── ProcessOrderItemWorkflow (Child) - Item 1
├── ProcessOrderItemWorkflow (Child) - Item 2
└── ProcessOrderItemWorkflow (Child) - Item 3
```

### What It Demonstrates

1. **Modularity**: Each order item is processed by a separate child workflow
2. **Reusability**: The child workflow can be used independently
3. **Isolation**: Each child workflow has its own execution history
4. **Parallel Potential**: Child workflows can be executed in parallel
5. **Aggregation**: Parent workflow collects results from all children

### Run

```bash
python MY/1_basic/child_workflow.py
```

### Expected Output

```
Order ORD-12345 completed:
  - Payment successful: $1139.96
  - Order ORD-12345 shipped to John Doe
  - Items processed: 3
```

## When to Use Child Workflows

### Good Use Cases

1. **Modular Components**: Breaking down complex workflows into smaller, reusable pieces
2. **Different Lifecycles**: When child tasks have different timeout or retry requirements
3. **Isolation**: When you want separate execution histories
4. **Versioning**: Different parts of the workflow may need different version strategies
5. **Parallel Processing**: When processing independent sub-tasks

### Example Scenarios

- **Order Processing**: Process each order item separately
- **Data Pipeline**: Each stage is a child workflow
- **Batch Jobs**: Each batch item processed by a child
- **Multi-tenant Operations**: Each tenant's workflow as a child
- **Complex Saga Patterns**: Each compensation step as a child

## Key Differences: Child Workflow vs Activity

### Child Workflow

- Can contain multiple activities
- Has its own workflow history
- Can be queried and signaled independently
- Survives worker restarts
- Better for complex, long-running tasks

### Activity

- Single unit of work
- No workflow features (can't wait, can't spawn children)
- Simpler and faster
- Better for quick operations

## Advanced Patterns

### Parallel Child Workflows

You can execute child workflows in parallel using `asyncio.gather()`:

```python
results = await asyncio.gather(*[
    workflow.execute_child_workflow(ChildWorkflow.run, item)
    for item in items
])
```

### Parent-Child Communication

- Child workflows can be signaled or queried
- Parent can wait for child with cancellation support
- Child inherits some parent properties (namespace, etc.)

---

### 2. Human in the Loop (`human_in_loop.py`)

Demonstrates workflows that pause for human decision-making.

**What It Demonstrates:**

- **Approval Workflows**: Waiting for human approval
- **Timeout Handling**: Auto-reject after 24 hours
- **Auto-Approval**: Automatic decisions for small amounts
- **Decision Signals**: `approve()` and `reject()` signals
- **Notifications**: Activities to notify humans

**Use Cases:**

- Expense approval systems
- Document review workflows
- Access request approvals
- Quality assurance gates
- Compliance reviews

**Run:**

```bash
python MY/1_basic/human_in_loop.py
```

**Expected Flow:**

```
Example 1: Small expense ($75) → Auto-approved
Example 2: Large expense ($2500) → Waits for approval → Manager approves
Example 3: Questionable expense ($5000) → Waits for approval → Manager rejects
```

---

## Key Concepts for Human-in-the-Loop

The human-in-the-loop pattern uses signals, queries, and wait conditions:

### Signals

**What are Signals?**

- One-way asynchronous messages to a running workflow
- Can carry data
- Do not return values
- Can be sent multiple times

**When to Use:**

- Updating workflow state
- Sending commands
- Responding to external events
- Human input/decisions

**Pattern:**

```python
@workflow.signal
async def my_signal(self, data: str) -> None:
    self._state = data
```

### Queries

**What are Queries?**

- Read-only operations on workflow state
- Synchronous
- Return values immediately
- Don't modify workflow state
- Work even after workflow completes

**When to Use:**

- Monitoring workflow progress
- Building dashboards
- Debugging
- Status checks

**Pattern:**

```python
@workflow.query
def get_state(self) -> str:
    return self._state
```

### Wait Conditions

**What are Wait Conditions?**

- Workflow pauses until a condition becomes true
- Can have timeouts
- Essential for human-in-the-loop patterns

**Pattern:**

```python
await workflow.wait_condition(
    lambda: self._is_ready,
    timeout=timedelta(hours=24)
)
```

## Signal vs Update

| Feature       | Signal          | Update           |
| ------------- | --------------- | ---------------- |
| Returns value | ❌ No           | ✅ Yes           |
| Blocks sender | ❌ No           | ✅ Yes           |
| Validation    | Limited         | Full validation  |
| Use case      | Fire and forget | Request/Response |

## Best Practices

### Signals

1. **Idempotency**: Handle duplicate signals gracefully
2. **Validation**: Validate signal data
3. **State Management**: Use proper state machines
4. **Error Handling**: Signals can't return errors, so handle internally

### Queries

1. **No Side Effects**: Queries must not modify state
2. **Fast**: Keep queries lightweight
3. **Determinism**: Return consistent results

### Human-in-the-Loop

1. **Timeouts**: Always have timeout fallbacks
2. **Notifications**: Notify humans reliably
3. **Reminders**: Send periodic reminders
4. **Escalation**: Escalate if no response
5. **Audit Trail**: Log all decisions

## Real-World Patterns

### Approval Workflow Pattern

```
1. Submit request
2. Auto-approve if meets criteria
3. Otherwise, notify approvers
4. Wait for approval signal (with timeout)
5. Process based on decision
6. Notify requester
```

### Interactive Processing Pattern

```
1. Start workflow
2. Wait for input signals
3. Process each input
4. Allow queries to monitor state
5. Complete when done signal received
```

### Escalation Pattern

```
1. Notify first approver
2. Wait N hours
3. If no response, escalate to manager
4. Wait N hours
5. If no response, auto-reject/auto-approve
```

## Common Pitfalls

1. **Query Side Effects**: Don't modify state in queries
2. **Missing Timeouts**: Always have timeout fallbacks
3. **Signal Ordering**: Don't assume signal arrival order
4. **State Races**: Properly synchronize state access
5. **Forgotten Notifications**: Always notify humans about required actions
