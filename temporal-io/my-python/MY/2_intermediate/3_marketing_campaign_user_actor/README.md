# Marketing Campaign Manager - User Actor Pattern Demo

This project demonstrates the **User Actor Pattern** in Temporal for managing shared state across multiple concurrent workflows.

## 🎯 What You'll Learn

### User Actor Pattern
- **One long-running workflow per user** (`user-actor-{user_id}`)
- **Single source of truth** for user state
- **Shared across ALL campaigns** for that user
- **Scales to millions** of concurrent users
- **Frequency capping** across all campaigns
- **Preference management** in one place

### Why User Actor Pattern?

**Problem**: Multiple marketing campaigns targeting same user
- Campaign A: Email campaign (Black Friday)
- Campaign B: SMS campaign (New feature)
- Campaign C: Push notification (Cart abandonment)

**Without User Actor**: Each campaign doesn't know about others
- Result: User gets bombarded with messages
- No unified frequency capping
- Duplicate state management

**With User Actor**: Single workflow coordinates all campaigns
- Result: Frequency caps enforced across ALL campaigns
- User preferences in one place
- Consistent experience

## 🏗️ Architecture

```
                    ┌─────────────────────────────┐
                    │   User Actor Workflow       │
                    │   (user-actor-USER123)      │
                    │                             │
                    │  State:                     │
                    │  - Message history          │
                    │  - Frequency caps           │
                    │  - Opt-out preferences      │
                    │  - Last message time        │
                    └─────────────────────────────┘
                              ▲       │
                    Query     │       │  Signal
                    (can send?│       │  (message sent)
                              │       ▼
        ┌────────────────┬────┴───────┴────┬────────────────┐
        │                │                  │                │
   ┌────▼─────┐    ┌────▼─────┐      ┌────▼─────┐    ┌────▼─────┐
   │Campaign A│    │Campaign B│      │Campaign C│    │Campaign D│
   │(Email)   │    │(SMS)     │      │(Push)    │    │(In-App)  │
   │Workflow  │    │Workflow  │      │Workflow  │    │Workflow  │
   └──────────┘    └──────────┘      └──────────┘    └──────────┘

All campaigns coordinate through the SAME User Actor!
```

## 🚀 Setup

```bash
# Navigate to project directory
cd /home/lukas/Projects/Github/temporalio/MY_PROJECTS/2_intermediate/3_marketing_campaign_user_actor

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv sync
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

The API will be available at http://localhost:8002

### 3. Run the Complete Demo

#### Step 1: Initialize User Actors

Create User Actor workflows for your users:

```bash
# Initialize User Actor for USER-001
curl -X POST http://localhost:8002/users/USER-001/init \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER-001",
    "max_messages_per_day": 3,
    "max_messages_per_week": 10,
    "max_messages_per_month": 30,
    "min_hours_between_messages": 2,
    "max_emails_per_week": 5,
    "max_sms_per_week": 3
  }'

# Initialize for USER-002
curl -X POST http://localhost:8002/users/USER-002/init \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER-002",
    "max_messages_per_day": 5,
    "max_messages_per_week": 15,
    "max_messages_per_month": 50,
    "min_hours_between_messages": 1,
    "max_emails_per_week": 10,
    "max_sms_per_week": 5
  }'
```

Response:
```json
{
  "message": "User actor initialized successfully",
  "user_id": "USER-001",
  "workflow_id": "user-actor-USER-001",
  "frequency_cap": {
    "max_messages_per_day": 3,
    "max_messages_per_week": 10,
    "max_messages_per_month": 30
  }
}
```

#### Step 2: Launch Campaign A - Email Campaign

```bash
curl -X POST http://localhost:8002/campaigns/launch \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "CAMP-EMAIL-001",
    "campaign_name": "Black Friday Sale",
    "campaign_type": "email",
    "priority": "high",
    "message_content": "🎉 Black Friday Sale! 50% off everything!",
    "target_user_ids": ["USER-001", "USER-002"],
    "metadata": {
      "discount": "50%",
      "expiry": "2025-11-30"
    }
  }'
```

#### Step 3: Check User State

See what messages the user has received:

```bash
curl http://localhost:8002/users/USER-001/state
```

Response:
```json
{
  "user_id": "USER-001",
  "total_messages_sent": 1,
  "last_message_time": "2025-01-31T16:00:00",
  "opted_out_channels": [],
  "preferences": {},
  "recent_messages": [
    {
      "timestamp": "2025-01-31T16:00:00",
      "campaign_id": "CAMP-EMAIL-001",
      "campaign_name": "Black Friday Sale",
      "campaign_type": "email",
      "success": true
    }
  ]
}
```

#### Step 4: Launch Campaign B - SMS Campaign

```bash
curl -X POST http://localhost:8002/campaigns/launch \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "CAMP-SMS-001",
    "campaign_name": "Flash Sale Alert",
    "campaign_type": "sms",
    "priority": "high",
    "message_content": "⚡ Flash Sale! Limited time offer!",
    "target_user_ids": ["USER-001", "USER-002"]
  }'
```

**The User Actor will check frequency caps before allowing this send!**

#### Step 5: Check Frequency Before Sending

```bash
curl -X POST http://localhost:8002/users/USER-001/check-frequency?campaign_type=push_notification
```

Response:
```json
{
  "user_id": "USER-001",
  "campaign_type": "push_notification",
  "allowed": true,
  "reason": "All frequency checks passed",
  "messages_sent_today": 2,
  "messages_sent_this_week": 2,
  "messages_sent_this_month": 2,
  "hours_since_last_message": 0.5
}
```

Or if frequency cap is hit:
```json
{
  "user_id": "USER-001",
  "campaign_type": "email",
  "allowed": false,
  "reason": "Minimum time between messages not met: 0.5h < 2h",
  "messages_sent_today": 2,
  "messages_sent_this_week": 2,
  "messages_sent_this_month": 2,
  "hours_since_last_message": 0.5
}
```

#### Step 6: Launch Multiple Campaigns Simultaneously

```bash
# Campaign C - Push Notification
curl -X POST http://localhost:8002/campaigns/launch \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "CAMP-PUSH-001",
    "campaign_name": "Cart Abandonment",
    "campaign_type": "push_notification",
    "priority": "medium",
    "message_content": "You left items in your cart!",
    "target_user_ids": ["USER-001", "USER-002"]
  }'

# Campaign D - In-App Message
curl -X POST http://localhost:8002/campaigns/launch \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "CAMP-INAPP-001",
    "campaign_name": "New Feature",
    "campaign_type": "in_app_message",
    "priority": "low",
    "message_content": "Check out our new feature!",
    "target_user_ids": ["USER-001", "USER-002"]
  }'
```

**All campaigns will coordinate through User Actor!**
- Some may be allowed
- Some may be skipped due to frequency caps
- User Actor maintains consistency

#### Step 7: Opt Out of a Channel

```bash
curl -X POST http://localhost:8002/users/USER-001/opt-out \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "sms"
  }'
```

Now USER-001 won't receive any SMS messages!

#### Step 8: Check Campaign Progress

```bash
curl http://localhost:8002/campaigns/CAMP-EMAIL-001/progress
```

Response:
```json
{
  "campaign_id": "CAMP-EMAIL-001",
  "campaign_name": "Black Friday Sale",
  "users_targeted": 2,
  "users_sent": 2,
  "users_skipped": 0
}
```

#### Step 9: Get Campaign Results

```bash
curl http://localhost:8002/campaigns/CAMP-EMAIL-001/result
```

Response:
```json
{
  "campaign_id": "CAMP-EMAIL-001",
  "campaign_name": "Black Friday Sale",
  "users_targeted": 2,
  "users_sent": 2,
  "users_skipped": 0,
  "results": [
    {
      "user_id": "USER-001",
      "sent": true,
      "success": true,
      "frequency_check": {
        "messages_today": 0,
        "messages_this_week": 0,
        "messages_this_month": 0
      }
    },
    {
      "user_id": "USER-002",
      "sent": true,
      "success": true,
      "frequency_check": {
        "messages_today": 0,
        "messages_this_week": 0,
        "messages_this_month": 0
      }
    }
  ]
}
```

## 🔍 How It Works

### Campaign Workflow Flow

For each user in campaign:
1. **Get User Actor handle**: `user-actor-{user_id}`
2. **Query**: Can we send? (`can_send_message`)
3. **If allowed**:
   - Send message via activity
   - **Signal** User Actor: `record_message_sent`
4. **If not allowed**:
   - Skip user
   - Log reason

### User Actor Workflow Flow

Long-running workflow that:
1. **Receives queries** from campaigns: "Can I send?"
2. **Checks frequency caps**:
   - Daily/weekly/monthly limits
   - Channel-specific limits
   - Minimum time between messages
   - Opt-out preferences
3. **Returns decision**: Allow or Deny
4. **Receives signals** when message sent
5. **Updates state**: Message history, counters, timestamps
6. **Runs indefinitely** (Continue-As-New after 30 days)

## 🎓 Key Concepts

### User Actor Pattern Benefits

| Aspect | Without User Actor | With User Actor |
|--------|-------------------|-----------------|
| **State Location** | Scattered across campaigns | Single workflow |
| **Consistency** | ❌ Race conditions possible | ✅ Guaranteed consistent |
| **Frequency Cap** | Per-campaign only | Across ALL campaigns |
| **Scalability** | Coordination overhead | Millions of users |
| **Debugging** | Check multiple places | One workflow to inspect |

### When to Use User Actor Pattern?

**Use when:**
- Multiple workflows need to coordinate on shared entity state
- Need frequency limiting across workflows
- Want single source of truth
- Entity has long-lived state (user, device, account)

**Examples:**
- Marketing: Frequency capping across campaigns
- Gaming: Player state across multiple game sessions
- IoT: Device state across multiple control workflows
- Banking: Account state across multiple transactions

### Workflow Coordination Patterns

```python
# Campaign Workflow queries User Actor
frequency_check = await user_actor_handle.query(
    UserActorWorkflow.can_send_message,
    message
)

if frequency_check.allowed:
    # Send message
    await send_message(user_id, message)

    # Tell User Actor we sent it
    await user_actor_handle.signal(
        UserActorWorkflow.record_message_sent,
        message,
        success=True
    )
```

### Continue-As-New for Long-Running Workflows

User Actor uses Continue-As-New to prevent unbounded history:

```python
# After 30 days, restart with same state
if self._days_running >= 30:
    workflow.continue_as_new(user_id, self._frequency_cap)
```

**Benefits:**
- Prevents event history from growing forever
- Maintains state across restarts
- Keeps workflow performant

## 🧪 Testing Scenarios

### Scenario 1: Frequency Cap Enforcement
1. Initialize user with max 3 messages/day
2. Launch 5 campaigns targeting same user
3. Only 3 will be sent, 2 will be skipped
4. Check user state - see exactly 3 messages

### Scenario 2: Channel-Specific Caps
1. Initialize user with max 5 emails/week
2. Launch 10 email campaigns
3. Only 5 emails sent
4. Launch SMS campaign - still works (different channel)

### Scenario 3: Minimum Time Between Messages
1. Send message at 10:00 AM
2. Try to send another at 10:30 AM (min 2 hours)
3. Second message skipped
4. Try again at 12:01 PM - succeeds

### Scenario 4: Opt-Out Handling
1. User opts out of SMS
2. Launch SMS campaign
3. User is skipped
4. Launch email campaign - still works

### Scenario 5: Multiple Concurrent Campaigns
1. Launch 4 campaigns simultaneously
2. All query same User Actor
3. User Actor enforces caps consistently
4. No race conditions

## 📊 View in Temporal UI

Open http://localhost:8233

**User Actor Workflow:**
- Workflow ID: `user-actor-USER-001`
- Shows all queries from campaigns
- Shows signals recording messages
- See complete message history

**Campaign Workflows:**
- Multiple campaign workflows running
- See external workflow calls to User Actor
- See which users were sent/skipped

## 💡 Best Practices Demonstrated

1. **Single Source of Truth**: One workflow owns user state
2. **Loose Coupling**: Campaigns don't know about each other
3. **Scalability**: Millions of users = millions of User Actors
4. **Idempotency**: Re-running campaign doesn't duplicate messages
5. **Continue-As-New**: Prevent unbounded history growth
6. **Query/Signal Pattern**: Read state (query), modify state (signal)
7. **Bounded History**: Keep only last 1000 messages
8. **Graceful Degradation**: Failed sends don't break workflow

## 🔗 API Documentation

Interactive API docs:
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

## 🆚 Alternative Approaches (and why they're worse)

### Approach 1: Shared Database
```
Campaign A ──┐
Campaign B ──┼─→ Database (user state)
Campaign C ──┘
```
**Problems:**
- Race conditions
- Need external locking
- No durability guarantees
- Complex retry logic

### Approach 2: Campaign Coordination Workflow
```
Campaign A ──┐
Campaign B ──┼─→ Coordinator Workflow ─→ User State
Campaign C ──┘
```
**Problems:**
- Coordinator becomes bottleneck
- Doesn't scale to millions of users
- Complex coordination logic

### Approach 3: User Actor (✅ Best)
```
Campaign A ──┐
Campaign B ──┼─→ User Actor (user-123) ─→ User State
Campaign C ──┘
```
**Benefits:**
- Natural partitioning by user
- No coordination bottleneck
- Temporal handles durability
- Scales linearly

## 🎯 Real-World Use Cases

1. **Marketing Automation** (this example)
   - Frequency capping across campaigns
   - Channel preferences
   - Unsubscribe management

2. **Gaming**
   - Player state across game sessions
   - Inventory management
   - Achievement tracking

3. **IoT Device Management**
   - Device state across control workflows
   - Rate limiting for device commands
   - Firmware update coordination

4. **Financial Services**
   - Account balance management
   - Transaction coordination
   - Fraud detection rules

5. **SaaS Platforms**
   - User quota management
   - Feature flag coordination
   - Usage tracking

## 📈 Scalability

**The User Actor pattern scales to millions because:**
- Each user = separate workflow
- Natural partitioning
- No cross-user coordination needed
- Temporal distributes across workers
- Continue-As-New prevents history growth

**Example:**
- 10 million users = 10 million User Actor workflows
- 100 campaigns = 100 Campaign workflows
- Total: 10,000,100 concurrent workflows ✅

Temporal handles this efficiently!
