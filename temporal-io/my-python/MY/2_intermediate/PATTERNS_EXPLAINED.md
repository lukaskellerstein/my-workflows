# Temporal Patterns - Visual Explanation

## Understanding Shared State in Temporal

### ❌ What NOT to Do (External Database)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Workflow A  │     │ Workflow B  │     │ Workflow C  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │    Race           │    Conditions     │
       │    Possible!      │    Locks?         │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Database   │
                    │  (external) │
                    └─────────────┘

Problems:
- Race conditions
- Need external locking
- No replay guarantees
- Complex retry logic
- State not in Temporal
```

### ✅ User Actor Pattern (THIS Solution)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Workflow A  │     │ Workflow B  │     │ Workflow C  │
│ (Campaign)  │     │ (Campaign)  │     │ (Campaign)  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │ Query             │ Query             │ Signal
       │ "Can send?"       │ "Can send?"       │ "Sent!"
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────────────────┐
                    │  User Actor Workflow    │
                    │  (user-actor-USER123)   │
                    │                         │
                    │  State:                 │
                    │  - Messages sent: 5     │
                    │  - Last message: 10:00  │
                    │  - Opted out: [SMS]     │
                    │                         │
                    │  Frequency Cap:         │
                    │  - Max/day: 10          │
                    │  - Min hours: 2         │
                    └─────────────────────────┘

Benefits:
✅ No race conditions (single workflow)
✅ Temporal handles durability
✅ State in event history
✅ Natural partitioning by user
✅ Scales to millions
```

---

## Pattern 1: Signals (One-Way Write)

### Use Case: External event triggers workflow action

```
┌──────────────────┐                    ┌──────────────────┐
│  Payment Gateway │                    │ Order Workflow   │
│                  │                    │                  │
│  Payment Success │                    │ [Waiting for     │
│                  │                    │  payment...]     │
│       ○          │                    │                  │
│       │          │                    │                  │
│       ▼          │                    │                  │
│   Webhook        │                    │                  │
│   Triggered      │                    │                  │
└────────┬─────────┘                    └────────▲─────────┘
         │                                       │
         │  Signal:                              │
         │  confirm_payment(payment_info)        │
         └───────────────────────────────────────┘
                     No response!
                     Fire & forget
```

**Characteristics:**
- Asynchronous
- No return value
- Recorded in history
- Workflow can wait for signal
- External system doesn't wait for result

**Example Code:**
```python
# Workflow
@workflow.signal
def confirm_payment(self, payment_info: PaymentInfo) -> None:
    self._payment_confirmed = True
    self._payment_info = payment_info

# Client
await handle.signal(OrderWorkflow.confirm_payment, payment_info)
# Returns immediately, no result
```

---

## Pattern 2: Queries (Read-Only)

### Use Case: Get current workflow state without modifying it

```
┌──────────────────┐                    ┌──────────────────┐
│  Dashboard       │                    │ Order Workflow   │
│                  │                    │                  │
│  [Show Status]   │                    │ Status: SHIPPED  │
│                  │                    │ ETA: Mar 15      │
│       ○          │                    │ Total: $999      │
│       │          │                    │                  │
│       ▼          │                    │                  │
│   Need Status    │                    │                  │
└────────┬─────────┘                    └────────▲─────────┘
         │                                       │
         │  Query: get_status()                  │
         │  ───────────────────────────────────▶ │
         │                                       │
         │  Response: "shipped"                  │
         │  ◀─────────────────────────────────── │
         │                                       │
         │  Query: get_eta()                     │
         │  ───────────────────────────────────▶ │
         │                                       │
         │  Response: "2025-03-15"               │
         │  ◀─────────────────────────────────── │
         └───────────────────────────────────────┘
```

**Characteristics:**
- Synchronous
- Returns value immediately
- NOT recorded in history
- Read-only (can't modify state)
- Works on completed workflows

**Example Code:**
```python
# Workflow
@workflow.query
def get_status(self) -> str:
    return self._status

@workflow.query
def get_eta(self) -> datetime:
    return self._estimated_delivery

# Client
status = await handle.query(OrderWorkflow.get_status)
eta = await handle.query(OrderWorkflow.get_eta)
```

---

## Pattern 3: Updates (Atomic Write + Read)

### Use Case: Submit approval AND get immediate feedback

```
┌──────────────────┐                    ┌──────────────────┐
│  Manager UI      │                    │ Approval         │
│                  │                    │ Workflow         │
│  [Approve Button]│                    │                  │
│       ○          │                    │ Status: PENDING  │
│       │          │                    │                  │
│       ▼          │                    │                  │
│   Click Approve  │                    │                  │
└────────┬─────────┘                    └────────▲─────────┘
         │                                       │
         │  Update:                              │
         │  submit_manager_approval(decision)    │
         │  ───────────────────────────────────▶ │
         │                                       │
         │           ┌─────────────────────┐     │
         │           │  1. Validate        │     │
         │           │  2. Update state    │     │
         │           │  3. Return state    │     │
         │           └─────────────────────┘     │
         │                                       │
         │  Response: {                          │
         │    status: "manager_approved",        │
         │    updated_at: "...",                 │
         │    manager_decision: {...}            │
         │  }                                    │
         │  ◀─────────────────────────────────── │
         └───────────────────────────────────────┘

         UI shows result immediately!
```

**Characteristics:**
- Synchronous
- Returns updated state
- Recorded in history
- Can validate before execution
- Atomic: validate → update → return

**Example Code:**
```python
# Workflow
@workflow.update
def submit_manager_approval(self, decision: ApprovalDecision) -> ApprovalState:
    # Update state
    self._manager_decision = decision
    self._status = ApprovalStatus.MANAGER_APPROVED
    # Return new state
    return self._get_current_state()

@workflow.update(name="submit_manager_approval")
def validate_manager_approval(self, decision: ApprovalDecision) -> None:
    # Runs BEFORE update handler
    if self._status != ApprovalStatus.PENDING:
        raise ApplicationError("Wrong status!")

# Client
updated_state = await handle.execute_update(
    HRApprovalWorkflow.submit_manager_approval,
    decision
)
# Gets updated state immediately!
```

---

## Pattern 4: User Actor (Shared State Coordinator)

### Full Example: Marketing Campaigns

```
Time: 10:00 AM
═══════════════════════════════════════════════════════════════

Campaign A (Email - Black Friday)
  │
  │ 1. Query User Actor: "Can I send to USER-123?"
  ▼
┌─────────────────────────────────────────────┐
│ User Actor (user-actor-USER-123)            │
│                                             │
│ Messages today: 0                           │
│ Max per day: 3                              │
│ Last message: null                          │
│                                             │
│ Decision: ✅ ALLOWED                        │
└─────────────────────────────────────────────┘
  │
  │ 2. Response: "Allowed!"
  ▼
Campaign A sends email
  │
  │ 3. Signal User Actor: "Email sent!"
  ▼
┌─────────────────────────────────────────────┐
│ User Actor (user-actor-USER-123)            │
│                                             │
│ Messages today: 1  ← Updated!               │
│ Max per day: 3                              │
│ Last message: 10:00 AM  ← Updated!          │
└─────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
Time: 10:30 AM (30 minutes later)
═══════════════════════════════════════════════════════════════

Campaign B (SMS - Flash Sale)
  │
  │ 1. Query User Actor: "Can I send to USER-123?"
  ▼
┌─────────────────────────────────────────────┐
│ User Actor (user-actor-USER-123)            │
│                                             │
│ Messages today: 1                           │
│ Max per day: 3                              │
│ Last message: 10:00 AM                      │
│ Min hours between: 2                        │
│                                             │
│ Time since last: 0.5 hours                  │
│                                             │
│ Decision: ❌ DENIED                         │
│ Reason: "Min 2 hours not met"               │
└─────────────────────────────────────────────┘
  │
  │ 2. Response: "Denied! Too soon."
  ▼
Campaign B skips USER-123
No message sent!

═══════════════════════════════════════════════════════════════
Time: 12:01 PM (2 hours 1 minute later)
═══════════════════════════════════════════════════════════════

Campaign C (Push - New Feature)
  │
  │ 1. Query User Actor: "Can I send to USER-123?"
  ▼
┌─────────────────────────────────────────────┐
│ User Actor (user-actor-USER-123)            │
│                                             │
│ Messages today: 1                           │
│ Max per day: 3                              │
│ Last message: 10:00 AM                      │
│ Min hours between: 2                        │
│                                             │
│ Time since last: 2.02 hours ✅              │
│                                             │
│ Decision: ✅ ALLOWED                        │
└─────────────────────────────────────────────┘
  │
  │ 2. Response: "Allowed!"
  ▼
Campaign C sends push notification
  │
  │ 3. Signal User Actor: "Push sent!"
  ▼
┌─────────────────────────────────────────────┐
│ User Actor (user-actor-USER-123)            │
│                                             │
│ Messages today: 2  ← Updated!               │
│ Max per day: 3                              │
│ Last message: 12:01 PM  ← Updated!          │
└─────────────────────────────────────────────┘
```

**Key Points:**
1. **Single Source of Truth**: User Actor owns all user state
2. **Coordination**: All campaigns check with User Actor first
3. **Consistency**: No race conditions, one workflow controls state
4. **Scalability**: One User Actor per user = natural partitioning

---

## When to Use Each Pattern

```
┌────────────────────────────────────────────────────────────┐
│ Decision Tree                                              │
└────────────────────────────────────────────────────────────┘

Need to interact with workflow state?
├─ Yes → Continue
└─ No → Just start workflow

Need to modify state?
├─ No → Use QUERY (read-only)
└─ Yes → Continue

Need immediate response?
├─ No → Use SIGNAL (fire & forget)
└─ Yes → Continue

Need to validate before modifying?
├─ Yes → Use UPDATE (with validator)
└─ No → Use UPDATE (simpler than Signal+Query)

Multiple workflows sharing entity state?
├─ Yes → Use USER ACTOR PATTERN
└─ No → Regular Signal/Query/Update is fine
```

---

## Real-World Scenarios

### Scenario 1: Order Processing
**Pattern**: Signals + Queries
- **Signal**: Payment confirmed
- **Query**: Get order status
- **Why**: External events (payments), monitoring needs

### Scenario 2: Multi-Step Approval
**Pattern**: Updates
- **Update**: Submit approval with validation
- **Why**: Need immediate feedback, enforce rules

### Scenario 3: Marketing Automation
**Pattern**: User Actor
- **User Actor**: Per-user frequency management
- **Why**: Multiple campaigns, shared user state

### Scenario 4: IoT Device Control
**Pattern**: User Actor
- **User Actor**: Per-device state (user-actor-DEVICE-123)
- **Multiple Control Workflows**: Temperature, security, maintenance
- **Why**: Device state shared across all control workflows

### Scenario 5: Banking Transactions
**Pattern**: User Actor
- **User Actor**: Per-account state (user-actor-ACCOUNT-456)
- **Multiple Transaction Workflows**: Deposits, withdrawals, transfers
- **Why**: Account balance coordination across transactions

---

## Common Mistakes

### ❌ Mistake 1: Using External DB for Coordination
```python
# DON'T DO THIS
async def run(self):
    # Checking external DB in workflow = bad!
    user_state = await db.get_user_state(user_id)  # ❌ Non-deterministic!
```

**Fix**: Use User Actor pattern

### ❌ Mistake 2: Using Signal When You Need Response
```python
# Workflow
@workflow.signal
def approve(self, decision):
    self._approved = True

# Client
await handle.signal(Workflow.approve, decision)
# Wait, did it work? What's the new state? 🤷
```

**Fix**: Use Update instead

### ❌ Mistake 3: Not Validating Updates
```python
# Can submit approval multiple times!
@workflow.update
def approve(self, decision):
    self._decision = decision  # ❌ No validation!
```

**Fix**: Add validator

### ❌ Mistake 4: Querying Completed Workflow for Critical Logic
```python
# ✅ Good: Read-only monitoring
status = await handle.query(get_status)

# ❌ Bad: Using query result for critical decision
if await handle.query(get_balance) > 100:
    # This could be wrong if workflow completed!
```

**Fix**: Use Update for critical operations

---

## Performance Comparison

| Operation | Latency | Use Case |
|-----------|---------|----------|
| **Signal** | ~10ms | Fire-and-forget updates |
| **Query** | ~5ms | Fast status checks |
| **Update** | ~20ms | Validated state changes |
| **User Actor Query** | ~5ms + lookup | Cross-workflow coordination |

All are extremely fast! Choose based on semantics, not performance.

---

## Summary

| I need to... | Use... | Example |
|--------------|--------|---------|
| Tell workflow something happened | Signal | Payment received |
| Check workflow state | Query | Get order status |
| Update state AND get result | Update | Approve with feedback |
| Share state across workflows | User Actor | Frequency capping |

**Golden Rule**:
- **Modify without response** → Signal
- **Read without modifying** → Query
- **Modify with response** → Update
- **Coordinate multiple workflows** → User Actor

All patterns are durable, scalable, and production-ready! 🚀
