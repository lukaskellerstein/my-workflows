# Human in the Loop Example

Demonstrates workflows that require human approval or decision-making. The workflow pauses and waits for human input via signals before continuing, showcasing Temporal's ability to handle long-running processes with external intervention.

## Architecture

This example separates concerns into distinct components:

- **`workflow_definitions.py`** - Workflow with signals/queries, activities, and data models
- **`worker.py`** - Worker script that processes approval workflows
- **`start_workflow.py`** - Python script with examples of starting workflows and sending signals
- **`api.py`** - FastAPI REST API for workflow management and human interaction

## Workflow Features

### Signals

- **`approve`** - Sent by approver to approve the expense
- **`reject`** - Sent by approver to reject the expense

### Queries

- **`get_status`** - Check current approval status (pending/approved/rejected/timeout)
- **`get_approval_decision`** - Get the approval decision details

### Approval Flow

1. **Validation** - Check expense against business rules
2. **Auto-Approval** - Amounts ≤ $100 are automatically approved
3. **Manual Approval** - Amounts > $100 require human decision
4. **Timeout** - Auto-reject after 24 hours if no decision
5. **Processing** - Execute approved expenses
6. **Notification** - Notify employee of decision

## Workflow Flow

```
Start → Validate → Auto-approve? → Process/Ship
                         ↓ No
                    Notify Approver
                         ↓
                   Wait for Signal (24h timeout)
                    ↙          ↘
              Approve         Reject
                ↓               ↓
             Process         Notify
                ↓               ↓
             Notify          Complete
                ↓
             Complete
```

## Prerequisites

1. Temporal server running locally on `localhost:7233`
2. Python dependencies installed via `uv sync`

## Usage

### 1. Start the Worker

The worker must be running to process approval workflows:

```bash
cd MY/1_basic_split/2_human_in_loop
uv run python worker.py
```

Output:
```
Connected to Temporal at localhost:7233
Worker started on task queue: 1-basic-human-in-loop-task-queue
Max concurrent activities: 5
Registered workflows:
  - ExpenseApprovalWorkflow (with signals and queries)
Registered activities:
  - validate_expense, notify_approver, process_approved_expense, notify_employee
Press Ctrl+C to stop the worker
```

### 2. Interact with Workflows

#### Option A: Python Script

The script includes comprehensive examples:

```bash
uv run python start_workflow.py
```

**Programmatic usage:**

```python
import asyncio
from start_workflow import (
    start_and_wait_workflow,
    start_workflow_with_manual_approval,
    send_approval,
    send_rejection,
    query_workflow_status
)
from workflow_definitions import ExpenseRequest

# Example 1: Auto-approval (small amount)
request = ExpenseRequest(
    employee="John Doe",
    amount=75.00,
    category="Office Supplies",
    description="Pens and notebooks"
)
result = asyncio.run(start_and_wait_workflow(request))

# Example 2: Manual approval required
request = ExpenseRequest(
    employee="Jane Smith",
    amount=2500.00,
    category="Travel",
    description="Conference attendance"
)
workflow_id = asyncio.run(start_workflow_with_manual_approval(request))

# Query status
asyncio.run(query_workflow_status(workflow_id))

# Send approval
asyncio.run(send_approval(
    workflow_id=workflow_id,
    approver="Manager Sarah",
    comments="Approved for Q1 budget"
))
```

#### Option B: FastAPI REST API

Start the API server:

```bash
uv run python api.py
```

The API will be available at `http://localhost:8003`

**Endpoints:**

1. **Health Check**
   ```bash
   curl http://localhost:8003/health
   ```

2. **Start Expense Approval**

   Small amount (auto-approved):
   ```bash
   curl -X POST http://localhost:8003/expense/start \
     -H "Content-Type: application/json" \
     -d '{
       "employee": "John Doe",
       "amount": 75.00,
       "category": "Office Supplies",
       "description": "Pens and notebooks"
     }'
   ```

   Large amount (requires approval):
   ```bash
   curl -X POST http://localhost:8003/expense/start \
     -H "Content-Type: application/json" \
     -d '{
       "employee": "Jane Smith",
       "amount": 2500.00,
       "category": "Travel",
       "description": "Conference attendance"
     }'
   ```

   Response:
   ```json
   {
     "workflow_id": "expense-approval-123e4567-e89b-12d3-a456-426614174000",
     "message": "Expense submitted. Waiting for manager approval.",
     "status": "pending_approval"
   }
   ```

3. **Check Status**
   ```bash
   curl http://localhost:8003/expense/{workflow_id}/status
   ```

4. **Approve Expense**
   ```bash
   curl -X POST http://localhost:8003/expense/{workflow_id}/approve \
     -H "Content-Type: application/json" \
     -d '{
       "approver": "Manager Sarah Johnson",
       "comments": "Approved for professional development"
     }'
   ```

5. **Reject Expense**
   ```bash
   curl -X POST http://localhost:8003/expense/{workflow_id}/reject \
     -H "Content-Type: application/json" \
     -d '{
       "approver": "Manager Sarah Johnson",
       "comments": "Budget constraints for this quarter"
     }'
   ```

6. **API Documentation**

   Interactive API docs available at:
   - Swagger UI: `http://localhost:8003/docs`
   - ReDoc: `http://localhost:8003/redoc`

## Configuration

All scripts use the following configuration:

- **Temporal Host**: `localhost:7233`
- **Task Queue**: `1-basic-human-in-loop-task-queue`
- **Max Concurrent Activities**: 5
- **API Port**: 8003
- **Approval Timeout**: 24 hours

To modify these, edit the constants at the top of each file.

## Example Scenarios

### Scenario 1: Auto-Approval (Small Amount)

**Input:**
```python
ExpenseRequest(
    employee="John Doe",
    amount=75.00,
    category="Office Supplies",
    description="Pens and notebooks"
)
```

**Flow:**
1. Validate expense ✓
2. Check amount: $75 ≤ $100 → Auto-approve
3. Process expense
4. Notify employee

**Result:**
```
Expense APPROVED by Auto-Approval System
Comments: Amount below $100 threshold
Expense of $75.0 processed for John Doe
```

### Scenario 2: Manual Approval (Large Amount)

**Input:**
```python
ExpenseRequest(
    employee="Jane Smith",
    amount=2500.00,
    category="Travel",
    description="Conference attendance"
)
```

**Flow:**
1. Validate expense ✓
2. Check amount: $2500 > $100 → Manual approval needed
3. Notify approver
4. **Wait for signal** (workflow pauses here)
5. Approver sends approval signal
6. Process expense
7. Notify employee

**Result:**
```
Expense APPROVED by Manager Sarah Johnson
Comments: Conference attendance is valuable for professional development
Expense of $2500.0 processed for Jane Smith
```

### Scenario 3: Rejection

**Input:**
```python
ExpenseRequest(
    employee="Bob Wilson",
    amount=5000.00,
    category="Equipment",
    description="Gaming setup"
)
```

**Flow:**
1. Validate expense ✓
2. Check amount: $5000 > $100 → Manual approval needed
3. Notify approver
4. **Wait for signal**
5. Approver sends rejection signal
6. Notify employee

**Result:**
```
Expense REJECTED: Gaming setup not related to business needs
```

### Scenario 4: Timeout (No Response)

**Flow:**
1. Validate expense ✓
2. Manual approval needed
3. Notify approver
4. **Wait for signal (24 hours)**
5. No response → Auto-reject
6. Notify employee

**Result:**
```
Expense REJECTED: No response within 24 hours
```

## Key Concepts

### Signals

Signals allow external systems or users to send data to running workflows. In this example:
- Approvers send `approve` or `reject` signals
- Workflows pause using `wait_condition` until signal received
- Signals can be sent via API, CLI, or programmatically

### Queries

Queries allow reading workflow state without affecting execution:
- Check approval status without interrupting the workflow
- Get decision details
- No side effects on workflow execution

### Timeouts

Workflows can wait with timeouts:
- 24-hour approval window
- Auto-reject if no response
- Prevents workflows from waiting indefinitely

## File Structure

```
2_human_in_loop/
├── workflow_definitions.py   # Workflow with signals/queries, activities
├── worker.py                  # Worker script
├── start_workflow.py          # Python workflow starter with signal examples
├── api.py                     # FastAPI workflow and signal API
└── README.md                  # This file
```

## Benefits of Human in the Loop

1. **Long-Running Processes**: Workflows can wait hours/days for human input
2. **External Integration**: Easy integration with approval systems
3. **Flexible Decision-Making**: Humans can override automated rules
4. **Audit Trail**: All decisions recorded in workflow history
5. **Timeout Protection**: Automatic handling of unresponsive approvers
6. **State Management**: Workflow maintains state while waiting

## Development Notes

- The worker must be running before starting workflows
- Workflows waiting for signals remain active in Temporal
- Signals can be sent from any Temporal client
- Queries don't affect workflow state
- Each signal/query must match the workflow definition
- Temporal UI shows signal and query history
- Auto-approval threshold can be adjusted in workflow code
- Timeout duration can be configured per use case

## Integration Ideas

This pattern works well with:
- Slack/Teams approval bots
- Email-based approval systems
- Web-based approval portals
- Mobile approval apps
- Automated approval rules engines
