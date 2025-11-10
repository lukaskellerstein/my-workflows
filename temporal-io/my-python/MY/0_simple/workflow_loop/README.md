# Workflow LOOP Examples

This folder demonstrates how to implement **LOOPS** in Temporal workflows, where the workflow can return to previous activities based on conditions.

## What is a LOOP in Workflows?

A **LOOP** means the workflow execution path goes through certain activities/nodes, and based on a condition evaluated later, it **returns back** to an earlier activity/node that was already executed.

```
Flow diagram:
┌─────────────┐
│  Activity A │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Activity B │
└──────┬──────┘
       │
       ▼
┌─────────────┐     NO (condition not met)
│  Activity C ├────────────────┐
│  (check)    │                │
└──────┬──────┘                │
       │ YES                   │
       │ (condition met)       │
       ▼                       │
┌─────────────┐                │
│  Activity D │                │
│  (finalize) │                │
└─────────────┘                │
       ▲                       │
       │                       │
       └───────────────────────┘
         LOOP BACK to Activity A
```

## Examples

### 1. `simple_loop.py` - Basic Loop Concept

The simplest demonstration of a loop:

- **Activity A**: Prepare data
- **Activity B**: Process data and generate a score
- **Activity C**: Check if score meets threshold (>= 80)
- **Loop Decision**: If score < 80, loop back to Activity A
- **Activity D**: Finalize (only when condition is met)

**Run:**
```bash
python simple_loop.py
```

**Expected behavior:**
- Attempt 1: Score = 30 → LOOP BACK
- Attempt 2: Score = 60 → LOOP BACK
- Attempt 3: Score = 90 → CONDITION MET → Proceed to finalization

### 2. `loop_with_retry.py` - Real-World Example

A practical document processing pipeline with quality checks:

**Flow:**
1. **Validate** document (once)
2. **Process** document
3. **Quality Check** - evaluate quality score
4. **Decision Point**:
   - If quality **passes** → Finalize
   - If quality **fails** → Loop back to processing with corrections
5. **Finalize** document

**Run:**
```bash
python loop_with_retry.py
```

**Features:**
- Demonstrates a real use case (document processing)
- Shows how to pass corrections/feedback in the loop
- Implements max attempts limit
- Two test cases included

### 3. `complex_multi_loop.py` - Advanced Multi-Loop Example ⭐

A **production-grade** e-commerce order fulfillment workflow with:
- **3 main loops** (Validation, Fulfillment, Delivery)
- **1 nested loop** (Packaging Quality inside Fulfillment)
- **15+ activities** across multiple phases
- **Visual Mermaid diagrams** showing complete workflow

**Flow:**
- **LOOP 1: Validation** - Customer verification, inventory check, payment auth
- **LOOP 2: Fulfillment** - Item picking with nested packaging quality loop
  - **LOOP 2A (Nested)**: Pack → Seal → Quality Check → Repack if fails
- **LOOP 3: Delivery** - Multiple delivery attempts with customer notifications

**Run:**
```bash
python complex_multi_loop.py
```

**Features:**
- Real-world e-commerce scenario
- Multiple decision points with conditional branching
- Nested loops demonstrating complex flow control
- Comprehensive logging showing all loop iterations
- Randomized failures for realistic testing
- Complete documentation in `COMPLEX_WORKFLOW_README.md`
- **Visual diagrams** in `workflow_diagram.md`

**See**: `workflow_diagram.md` for complete Mermaid flowcharts and `COMPLEX_WORKFLOW_README.md` for detailed documentation.

## Key Concepts

### 1. Loop Implementation in Temporal

```python
@workflow.defn
class LoopWorkflow:
    @workflow.run
    async def run(self):
        max_attempts = 5
        attempt = 0

        # This is the loop
        while attempt < max_attempts:
            attempt += 1

            # Execute activities
            result_a = await workflow.execute_activity(activity_a, attempt, ...)
            result_b = await workflow.execute_activity(activity_b, result_a, ...)
            condition = await workflow.execute_activity(check_condition, result_b, ...)

            # Decision point
            if condition:
                break  # Exit loop
            # else: loop continues (goes back to start of while)

        # Continue after loop
        await workflow.execute_activity(finalize, ...)
```

### 2. Why Use Loops?

- **Retry with modifications**: Process → Check → Re-process with corrections
- **Iterative improvement**: Keep processing until quality threshold is met
- **Approval workflows**: Submit → Review → Revise → Re-submit
- **Polling patterns**: Check status → Wait → Check again

### 3. Best Practices

1. **Always set max attempts**: Prevent infinite loops
   ```python
   max_attempts = 5
   attempt = 0
   while attempt < max_attempts:
       attempt += 1
       # ...
   ```

2. **Use workflow state**: Pass data between iterations
   ```python
   corrections = None
   while attempt < max_attempts:
       result = await process(data, corrections)
       if quality_check(result):
           break
       corrections = generate_corrections(result)
   ```

3. **Log loop iterations**: Make debugging easier
   ```python
   workflow.logger.info(f"Loop iteration {attempt}/{max_attempts}")
   ```

4. **Handle loop exhaustion**: Define behavior when max attempts reached
   ```python
   if attempt >= max_attempts:
       return "Failed after max attempts"
   ```

## Running the Examples

### Prerequisites

1. Start Temporal server:
   ```bash
   temporal server start-dev
   ```

2. Ensure you're in the right directory:
   ```bash
   cd MY/0_simple/workflow_loop
   ```

### Run Examples

```bash
# Simple loop example
python simple_loop.py

# Document processing with loop
python loop_with_retry.py

# Complex multi-loop example (recommended!)
python complex_multi_loop.py
```

## Viewing in Temporal UI

1. Open Temporal UI: http://localhost:8233
2. Look for workflows:
   - `simple-loop-workflow`
   - `workflow-loop-test-1`
   - `workflow-loop-test-2`
   - `complex-multi-loop-workflow` ⭐
3. Click on a workflow to see:
   - Activity execution history
   - How many times activities were executed
   - The loop iterations in the event history
   - Visual timeline showing loop patterns

## Common Patterns

### Pattern 1: Retry Until Success
```python
while not success and attempt < max_attempts:
    result = await execute_activity(...)
    success = check_result(result)
```

### Pattern 2: Retry with Feedback
```python
feedback = None
while attempt < max_attempts:
    result = await execute_activity(..., feedback)
    if result.ok:
        break
    feedback = result.corrections
```

### Pattern 3: Approval Loop
```python
approved = False
while not approved and attempt < max_attempts:
    await submit_for_review(...)
    approval = await wait_for_approval(...)
    if approval.approved:
        approved = True
    else:
        await apply_feedback(approval.comments)
```

## Differences from Simple Iteration

**Simple Iteration** (like `../loop.py`):
```python
# Process list of items sequentially - NO loop back
for item in items:
    await workflow.execute_activity(process, item, ...)
```

**Conditional Loop** (these examples):
```python
# Can return to previous activities based on conditions
while not condition_met:
    await workflow.execute_activity(activity_a, ...)
    await workflow.execute_activity(activity_b, ...)
    condition_met = await workflow.execute_activity(check, ...)
    # If condition_met is False, loops back to activity_a
```

## Next Steps

- Modify `simple_loop.py` to change the threshold or max attempts
- Add more activities to the loop in `loop_with_retry.py`
- Implement your own use case (e.g., API polling, approval workflow)
- Experiment with nested loops or multiple loop conditions
