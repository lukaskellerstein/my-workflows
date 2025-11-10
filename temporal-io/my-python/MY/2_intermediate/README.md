# Temporal Intermediate Patterns - Complete Guide

This folder contains three comprehensive real-world projects demonstrating advanced Temporal patterns: **Signals, Queries, Updates, and the User Actor Pattern**.

## 📚 Projects Overview

### 1. E-commerce Order Processing (Signals + Queries)
**Location**: `1_ecommerce_order_processing/`

Demonstrates how external systems interact with running workflows:
- **Signals**: Payment gateway sends payment confirmation, users cancel orders
- **Queries**: Check order status, get delivery estimates, retrieve full order details
- **Use Case**: Complete order lifecycle from creation to delivery

**Key Learning**: Read/write operations on workflow state from external systems

[📖 Full Documentation](./1_ecommerce_order_processing/README.md)

---

### 2. HR Approval Workflow (Updates)
**Location**: `2_hr_approval_slack/`

Demonstrates the new Updates pattern - atomic read+write operations:
- **Updates**: Manager/HR approvals with immediate state feedback
- **Validators**: Enforce business rules before state changes
- **Slack Integration**: Real-world approval notifications
- **Use Case**: Multi-level approval workflow

**Key Learning**: Updates = Signals + Queries in one atomic operation

[📖 Full Documentation](./2_hr_approval_slack/README.md)

---

### 3. Marketing Campaign Manager (User Actor Pattern)
**Location**: `3_marketing_campaign_user_actor/`

Demonstrates managing shared state across multiple concurrent workflows:
- **User Actor**: One long-running workflow per user
- **Frequency Capping**: Coordinate message sends across ALL campaigns
- **Scalability**: Millions of concurrent user workflows
- **Use Case**: Marketing automation with intelligent frequency control

**Key Learning**: How to share state across workflows without external databases

[📖 Full Documentation](./3_marketing_campaign_user_actor/README.md)

---

## 🎯 Learning Path

### Recommended Order:

1. **Start with Project 1** (E-commerce)
   - Learn basic Signals and Queries
   - Understand external workflow interaction
   - Simple to understand, real-world use case

2. **Then Project 2** (HR Approval)
   - Learn Updates (evolution of Signals)
   - Understand validators
   - See why Updates are better than Signal+Query

3. **Finally Project 3** (Marketing)
   - Learn User Actor pattern
   - Understand workflow coordination
   - See how to scale to millions of users

## 🔑 Key Concepts Comparison

### Signals vs Queries vs Updates

| Feature | Signal | Query | Update |
|---------|--------|-------|--------|
| **Purpose** | Modify state | Read state | Modify + Read |
| **Direction** | External → Workflow | Workflow → External | Bidirectional |
| **Returns Value** | ❌ No | ✅ Yes | ✅ Yes |
| **Modifies State** | ✅ Yes | ❌ No | ✅ Yes |
| **Validation** | ❌ No | N/A | ✅ Yes |
| **Recorded in History** | ✅ Yes | ❌ No | ✅ Yes |
| **Blocking** | ❌ Async | ✅ Sync | ✅ Sync |
| **Use When** | Fire-and-forget | Monitoring | Need feedback |

### When to Use Each Pattern

**Signals** (Project 1):
- Fire-and-forget updates
- Don't need immediate response
- Simple state changes
- Example: "Cancel this order"

**Queries** (Project 1):
- Read current state
- Monitoring dashboards
- Status checks
- Example: "What's the order status?"

**Updates** (Project 2):
- Need confirmation after update
- Want validation before execution
- Critical user interactions
- Example: "Approve and tell me the result"

**User Actor** (Project 3):
- Multiple workflows share entity state
- Need coordination across workflows
- Long-lived entity state
- Example: "Coordinate all campaigns for this user"

## 🚀 Quick Start

### Prerequisites

All projects require:
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Start Temporal server
temporal server start-dev
```

### Run Any Project

Each project follows the same structure:

```bash
# 1. Navigate to project
cd 1_ecommerce_order_processing  # or 2_hr_approval_slack or 3_marketing_campaign_user_actor

# 2. Setup environment
uv venv
source .venv/bin/activate
uv sync

# 3. Start worker (Terminal 1)
uv run python worker.py

# 4. Start API (Terminal 2)
uv run python api.py

# 5. Follow project-specific README for usage examples
```

## 🏗️ Project Structure

Each project contains:

```
project-name/
├── pyproject.toml          # Dependencies (uv)
├── README.md               # Project-specific documentation
├── models.py               # Data models
├── activities.py           # Temporal activities (business logic)
├── workflows.py            # Temporal workflows (orchestration)
├── worker.py               # Temporal worker
├── api.py                  # FastAPI REST API
└── .env.example           # Environment variables (if needed)
```

## 📊 Visual Comparison

### Pattern 1: Signal + Query (Project 1)
```
┌─────────────┐                    ┌─────────────┐
│   Client    │────Signal─────────▶│  Workflow   │
│             │                    │             │
│             │◀───No Response─────│             │
│             │                    │             │
│             │────Query──────────▶│             │
│             │◀───State───────────│             │
└─────────────┘                    └─────────────┘

Two calls: Signal (write) + Query (read)
```

### Pattern 2: Update (Project 2)
```
┌─────────────┐                    ┌─────────────┐
│   Client    │────Update─────────▶│  Workflow   │
│             │                    │  Validator  │
│             │◀───Updated State───│  Handler    │
└─────────────┘                    └─────────────┘

One call: Write + Read atomically
```

### Pattern 3: User Actor (Project 3)
```
┌──────────────┐      Query      ┌────────────────┐
│ Campaign A   │────(can send?)──▶│   User Actor   │
└──────────────┘                  │  (user-123)    │
┌──────────────┐      Signal     │                │
│ Campaign B   │────(msg sent)───▶│  - State       │
└──────────────┘                  │  - Freq caps   │
┌──────────────┐      Query      │  - Preferences │
│ Campaign C   │────(can send?)──▶│                │
└──────────────┘                  └────────────────┘

Multiple workflows coordinate through one actor
```

## 🎓 Advanced Topics Covered

### Project 1 (E-commerce)
- ✅ External event handling (payments, cancellations)
- ✅ Workflow timeouts (24h payment window)
- ✅ Compensation logic (refunds, inventory release)
- ✅ Activity retries with backoff
- ✅ Email notifications
- ✅ State queries on completed workflows

### Project 2 (HR Approval)
- ✅ Multi-level approval chains
- ✅ Update validators (business rule enforcement)
- ✅ Atomic operations (approve + get state)
- ✅ Slack integration (optional)
- ✅ Comment tracking
- ✅ Approval audit trail

### Project 3 (Marketing)
- ✅ Long-running workflows (indefinite)
- ✅ Continue-As-New pattern
- ✅ Workflow-to-workflow communication
- ✅ External workflow handles
- ✅ Frequency capping algorithms
- ✅ Concurrent workflow coordination
- ✅ Scalability patterns (millions of workflows)

## 💡 Real-World Applications

### E-commerce (Project 1)
- Order processing
- Booking systems
- Reservation management
- Payment flows

### Approval Workflows (Project 2)
- HR approvals
- Expense reimbursements
- Contract reviews
- Change management
- Compliance workflows

### User Actor Pattern (Project 3)
- Marketing automation
- Gaming (player state)
- IoT (device management)
- Banking (account state)
- SaaS platforms (quota management)

## 🔍 Debugging Tips

### View Workflows in Temporal UI
```bash
# Open browser
http://localhost:8233

# Find workflows by ID:
# Project 1: order-ORD-20250131-143022
# Project 2: approval-REQ-20250131-153022
# Project 3: user-actor-USER-001
```

### Common Issues

**Worker not processing workflows?**
```bash
# Check worker is running
# Check task queue matches: "order-processing-queue", "hr-approval-queue", "marketing-campaign-queue"
```

**Workflow not found?**
```bash
# Use correct workflow ID format
# Check workflow was started successfully
# Verify temporal server is running
```

**Signal/Query/Update failed?**
```bash
# Check workflow is still running (not completed)
# Verify correct handler name
# Check parameter types match
```

## 📚 Additional Resources

### Temporal Documentation
- [Signals](https://docs.temporal.io/signals)
- [Queries](https://docs.temporal.io/queries)
- [Updates](https://docs.temporal.io/updates)
- [Continue-As-New](https://docs.temporal.io/continue-as-new)

### Best Practices
- [Workflow Design Patterns](https://docs.temporal.io/workflows#workflow-design-patterns)
- [Activity Best Practices](https://docs.temporal.io/activities#activity-best-practices)
- [Testing Workflows](https://docs.temporal.io/testing)

## 🎯 Next Steps

After completing these projects, you'll understand:
- ✅ How to interact with running workflows
- ✅ When to use Signals vs Queries vs Updates
- ✅ How to coordinate multiple workflows
- ✅ How to scale to millions of concurrent workflows
- ✅ Real-world patterns for production systems

**Advanced Topics** (not covered here):
- Child workflows
- Saga pattern for distributed transactions
- Versioning workflows
- Testing strategies
- Deployment patterns

## 🤝 Contributing

Each project is self-contained and fully functional. Feel free to:
- Modify frequency caps
- Add new campaign types
- Integrate real Slack
- Add more approval levels
- Experiment with patterns

## 📝 Summary

| Project | Pattern | API Port | Key Feature |
|---------|---------|----------|-------------|
| E-commerce | Signals + Queries | 8000 | External events |
| HR Approval | Updates | 8001 | Atomic feedback |
| Marketing | User Actor | 8002 | Shared state |

**All projects demonstrate production-ready patterns you can use today!**

---

Happy learning! 🚀

For questions or issues, refer to individual project READMEs or [Temporal Community](https://community.temporal.io).
