# HR Approval Workflow - Temporal Updates Demo

This project demonstrates **Temporal Updates** through a real-world HR approval workflow with Slack integration.

## 🎯 What You'll Learn

### Updates (Write + Read Combined)
- **submit_manager_approval**: Manager approves/rejects with instant feedback
- **submit_hr_approval**: HR provides final approval with updated state
- **add_comments**: Add comments and get confirmation
- Updates = **Signal + Query in one atomic operation**
- Includes validation before execution
- Returns updated state immediately

### Why Updates > Signals?
- **Immediate Feedback**: Get updated state without separate query
- **Validation**: Reject invalid operations before execution
- **Atomicity**: State change + response in single operation
- **Better UX**: Client gets confirmation immediately

## 🏗️ Architecture

```
┌──────────────┐      ┌──────────────┐      ┌─────────────────┐
│   REST API   │─────▶│   Temporal   │◀─────│  HR Workflow    │
│  (FastAPI)   │      │   Server     │      │  (2-level       │
│              │      │              │      │   approval)     │
└──────────────┘      └──────────────┘      └─────────────────┘
                             │                       │
                             │                       ▼
                      ┌──────┴───────┐      ┌─────────────────┐
                      │    Slack     │      │   Activities    │
                      │  (optional)  │      │ (Notifications) │
                      └──────────────┘      └─────────────────┘
```

## 🚀 Setup

```bash
# Navigate to project directory
cd /home/lukas/Projects/Github/temporalio/MY_PROJECTS/2_intermediate/2_hr_approval_slack

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv sync

# Optional: Configure Slack
cp .env.example .env
# Edit .env with your Slack credentials (or skip for demo mode)
```

## 📋 Prerequisites

Make sure Temporal server is running:
```bash
temporal server start-dev
```

## 🎮 Usage

### 1. Start the Worker

In terminal 1:
```bash
source .venv/bin/activate
uv run python worker.py
```

### 2. Start the REST API

In terminal 2:
```bash
source .venv/bin/activate
uv run python api.py
```

The API will be available at http://localhost:8001

### 3. Submit and Approve Requests

#### Create Approval Request

```bash
curl -X POST http://localhost:8001/requests \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "EMP-001",
    "employee_name": "John Doe",
    "request_type": "time_off",
    "title": "Vacation - Hawaii",
    "description": "Family vacation to Hawaii",
    "priority": "medium",
    "start_date": "2025-03-01T00:00:00",
    "end_date": "2025-03-10T00:00:00"
  }'
```

Response:
```json
{
  "request_id": "REQ-20250131-153022",
  "workflow_id": "approval-REQ-20250131-153022",
  "status": "pending",
  "message": "Approval request created. Awaiting manager approval."
}
```

#### Manager Approval (UPDATE - Atomic Write + Read)

```bash
curl -X POST http://localhost:8001/requests/REQ-20250131-153022/manager-approval \
  -H "Content-Type: application/json" \
  -d '{
    "approver_id": "MGR-001",
    "approver_name": "Sarah Manager",
    "approved": true,
    "comments": "Approved. Enjoy your vacation!"
  }'
```

Response (immediate feedback with updated state):
```json
{
  "request_id": "REQ-20250131-153022",
  "message": "Manager approved the request",
  "updated_state": {
    "status": "manager_approved",
    "updated_at": "2025-01-31T15:31:00",
    "manager_decision": {
      "approver": "Sarah Manager",
      "approved": true,
      "comments": "Approved. Enjoy your vacation!"
    }
  }
}
```

#### Query Status (READ-ONLY)

```bash
curl http://localhost:8001/requests/REQ-20250131-153022/status
```

#### HR Approval (UPDATE - Final Approval)

```bash
curl -X POST http://localhost:8001/requests/REQ-20250131-153022/hr-approval \
  -H "Content-Type: application/json" \
  -d '{
    "approver_id": "HR-001",
    "approver_name": "Linda HR",
    "approved": true,
    "comments": "Time off approved in system"
  }'
```

Response (complete updated state):
```json
{
  "request_id": "REQ-20250131-153022",
  "message": "HR approved the request",
  "final_status": "hr_approved",
  "updated_state": {
    "status": "hr_approved",
    "updated_at": "2025-01-31T15:32:00",
    "completed_at": "2025-01-31T15:32:00",
    "hr_decision": {
      "approver": "Linda HR",
      "approved": true,
      "comments": "Time off approved in system"
    }
  }
}
```

#### Add Comments (Lightweight UPDATE)

```bash
curl -X POST http://localhost:8001/requests/REQ-20250131-153022/comments \
  -H "Content-Type: application/json" \
  -d '{
    "commenter_name": "John Doe",
    "comments": "Thanks for the quick approval!"
  }'
```

#### Cancel Request (SIGNAL)

```bash
curl -X DELETE http://localhost:8001/requests/REQ-20250131-153022 \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Plans changed"
  }'
```

#### Get Full Request Details (QUERY)

```bash
curl http://localhost:8001/requests/REQ-20250131-153022
```

## 🔍 Workflow Flow

```
1. Request Created → Status: pending
   ↓
2. Manager Reviews
   ├─ APPROVED → Status: manager_approved
   │   └─→ Goes to HR
   └─ REJECTED → Status: rejected (END)

3. HR Reviews
   ├─ APPROVED → Status: hr_approved
   │   └─→ Resource Provisioned
   └─ REJECTED → Status: rejected (END)

4. Resource Provisioned
   └─→ Employee Notified
```

## 🎓 Key Concepts: Updates vs Signals vs Queries

### Comparison Table

| Feature | Signal | Query | Update |
|---------|--------|-------|--------|
| **Purpose** | Write (modify state) | Read (get state) | Write + Read |
| **Returns Value** | ❌ No | ✅ Yes | ✅ Yes |
| **Modifies State** | ✅ Yes | ❌ No | ✅ Yes |
| **Validation** | ❌ No | ❌ N/A | ✅ Yes (Validator) |
| **Recorded** | ✅ Yes | ❌ No | ✅ Yes |
| **Blocking** | ❌ No | ✅ Yes | ✅ Yes |
| **When Workflow Closed** | ❌ Cannot send | ✅ Can query | ❌ Cannot send |

### When to Use Each

**Use SIGNAL when:**
- Fire-and-forget operations
- Don't need immediate feedback
- Simple state updates
- Example: "Cancel this workflow"

**Use QUERY when:**
- Read-only access to state
- No state modification needed
- Monitoring/dashboard displays
- Example: "What's the current status?"

**Use UPDATE when:**
- Need immediate feedback after state change
- Want to validate before execution
- Need atomic write + read operation
- Critical user interactions
- Example: "Submit approval and tell me the new state"

## 💡 Update Validators

Updates can have validators that run BEFORE the update handler:

```python
@workflow.update
def submit_manager_approval(self, decision: ApprovalDecision) -> ApprovalState:
    # This runs SECOND
    self._manager_decision = decision
    return self._get_current_state()

@workflow.update(name="submit_manager_approval")
def validate_manager_approval(self, decision: ApprovalDecision) -> None:
    # This runs FIRST - can reject invalid updates
    if self._status != ApprovalStatus.PENDING:
        raise ApplicationError("Wrong status!")
```

**Validator Benefits:**
- Reject invalid updates before execution
- Prevent invalid state transitions
- Provide clear error messages
- Maintain workflow invariants

## 🧪 Testing Scenarios

### Happy Path - Full Approval
1. Create request
2. Manager approves (UPDATE) → Get updated state
3. HR approves (UPDATE) → Get final state
4. Resource provisioned automatically

### Manager Rejection
1. Create request
2. Manager rejects (UPDATE) → Get rejection state
3. Workflow ends (no HR step needed)

### HR Rejection
1. Create request
2. Manager approves
3. HR rejects (UPDATE) → Get rejection state
4. Workflow ends

### Invalid Update (Validation Fails)
1. Create request
2. Try to submit HR approval before manager → ERROR
3. Validator rejects the update

### Add Comments During Review
1. Create request
2. Add comments (UPDATE) → Get confirmation
3. Continue with approvals

### Cancel Request
1. Create request
2. Cancel (SIGNAL) before any approval
3. Check status → "cancelled"

## 🔗 Slack Integration (Optional)

If you configure Slack credentials in `.env`:

1. Notifications sent to Slack channel
2. Approvers notified in real-time
3. Can integrate Slack buttons for approvals
4. Employee gets DM notifications

Without Slack configuration, all notifications are logged (demo mode).

## 📊 View in Temporal UI

Open http://localhost:8233 to see:
- Workflow execution with 2-level approval
- Update events recorded in history
- Validator rejections (if any)
- Activity executions for notifications
- Complete audit trail

## 🎯 Best Practices Demonstrated

1. **Update Validators**: Enforce business rules before state changes
2. **Immediate Feedback**: Users get updated state without separate query
3. **Atomic Operations**: State change + response in single transaction
4. **Multi-Level Approval**: Chain approvals with proper state management
5. **Graceful Degradation**: Works without Slack (demo mode)
6. **Timeout Handling**: 48h for manager, 72h for HR
7. **Clear State Machine**: Well-defined status transitions

## 🔗 API Documentation

Interactive API docs:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## 🆚 Comparison: Update vs Signal+Query

**Old Way (Signal + Query):**
```bash
# Send signal
curl -X POST .../manager-approval
# Response: OK

# Then query to see result
curl .../status
# Response: {"status": "manager_approved"}
```

**New Way (Update):**
```bash
# Send update
curl -X POST .../manager-approval
# Response: {"status": "manager_approved", "updated_at": "...", ...}
# Get result immediately!
```

**Benefits:**
- One HTTP call instead of two
- Guaranteed consistency
- Better user experience
- Validation before execution
