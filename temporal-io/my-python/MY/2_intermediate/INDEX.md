# Complete Documentation Index

All documentation files for the Temporal Intermediate Patterns project.

## 📚 Start Here

1. **[README.md](./README.md)** - Main overview of all three projects
2. **[QUICK_START.md](./QUICK_START.md)** - Get running in 30 seconds

## 🎓 Learn the Concepts

3. **[PATTERNS_EXPLAINED.md](./PATTERNS_EXPLAINED.md)** - Visual explanation of all patterns
   - What is shared state?
   - When to use Signals vs Queries vs Updates
   - User Actor pattern explained
   - Real-world examples with diagrams

## 🔧 When Things Go Wrong

4. **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Solutions to common issues
   - Connection problems
   - Workflow not starting
   - API errors
   - Performance issues

## 📦 Project-Specific Documentation

### Project 1: E-commerce Order Processing
- **[1_ecommerce_order_processing/README.md](./1_ecommerce_order_processing/README.md)**
- Pattern: Signals + Queries
- Port: 8000
- Focus: External event handling

### Project 2: HR Approval Workflow
- **[2_hr_approval_slack/README.md](./2_hr_approval_slack/README.md)**
- Pattern: Updates
- Port: 8001
- Focus: Atomic operations with validation

### Project 3: Marketing Campaign Manager
- **[3_marketing_campaign_user_actor/README.md](./3_marketing_campaign_user_actor/README.md)**
- Pattern: User Actor
- Port: 8002
- Focus: Shared state coordination

## 📖 Reading Order for Maximum Learning

**Complete Beginner?**
1. Start with [QUICK_START.md](./QUICK_START.md) - Get Project 1 running
2. Read [Project 1 README](./1_ecommerce_order_processing/README.md) - Understand Signals/Queries
3. Read [PATTERNS_EXPLAINED.md](./PATTERNS_EXPLAINED.md) - Solidify concepts
4. Run Project 2, read its README - Learn Updates
5. Run Project 3, read its README - Learn User Actor
6. Keep [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) handy

**Already Know Temporal Basics?**
1. Skim [README.md](./README.md) - See what's covered
2. Jump to [PATTERNS_EXPLAINED.md](./PATTERNS_EXPLAINED.md) - Quick concept review
3. Pick the project most relevant to you
4. Run it, read its README

**Just Need a Reference?**
1. [PATTERNS_EXPLAINED.md](./PATTERNS_EXPLAINED.md) - Pattern decision tree
2. [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues
3. Project READMEs - API examples

## 🎯 Quick Reference

### Pattern Decision Tree

```
Need to interact with workflow?
├─ Read state → QUERY
├─ Write state (no response) → SIGNAL
├─ Write state (need response) → UPDATE
└─ Share state across workflows → USER ACTOR
```

### Project Ports

- Project 1: `http://localhost:8000`
- Project 2: `http://localhost:8001`
- Project 3: `http://localhost:8002`
- Temporal UI: `http://localhost:8233`

### Quick Commands

```bash
# Start any project
cd [project-dir]
uv venv && source .venv/bin/activate && uv sync

# Terminal 1: Worker
uv run python worker.py

# Terminal 2: API
uv run python api.py

# View workflows
open http://localhost:8233
```

## 📊 Documentation Map

```
2_intermediate/
│
├─ README.md ...................... Main overview
├─ QUICK_START.md ................. 30-second setup
├─ PATTERNS_EXPLAINED.md .......... Visual concept guide
├─ TROUBLESHOOTING.md ............. Problem solutions
├─ INDEX.md (this file) ........... Documentation index
│
├─ 1_ecommerce_order_processing/
│  ├─ README.md ................... Project 1 docs
│  ├─ pyproject.toml
│  ├─ models.py
│  ├─ activities.py
│  ├─ workflows.py
│  ├─ worker.py
│  └─ api.py
│
├─ 2_hr_approval_slack/
│  ├─ README.md ................... Project 2 docs
│  ├─ pyproject.toml
│  ├─ .env.example
│  ├─ models.py
│  ├─ activities.py
│  ├─ workflows.py
│  ├─ worker.py
│  └─ api.py
│
└─ 3_marketing_campaign_user_actor/
   ├─ README.md .................... Project 3 docs
   ├─ pyproject.toml
   ├─ models.py
   ├─ activities.py
   ├─ user_actor_workflow.py
   ├─ campaign_workflow.py
   ├─ worker.py
   └─ api.py
```

## 🔍 Search Index

Looking for information about...

**Signals?**
- [PATTERNS_EXPLAINED.md](./PATTERNS_EXPLAINED.md#pattern-1-signals-one-way-write)
- [Project 1 README](./1_ecommerce_order_processing/README.md)

**Queries?**
- [PATTERNS_EXPLAINED.md](./PATTERNS_EXPLAINED.md#pattern-2-queries-read-only)
- [Project 1 README](./1_ecommerce_order_processing/README.md)

**Updates?**
- [PATTERNS_EXPLAINED.md](./PATTERNS_EXPLAINED.md#pattern-3-updates-atomic-write--read)
- [Project 2 README](./2_hr_approval_slack/README.md)

**User Actor?**
- [PATTERNS_EXPLAINED.md](./PATTERNS_EXPLAINED.md#pattern-4-user-actor-shared-state-coordinator)
- [Project 3 README](./3_marketing_campaign_user_actor/README.md)

**Shared State?**
- [PATTERNS_EXPLAINED.md](./PATTERNS_EXPLAINED.md#understanding-shared-state-in-temporal)
- [Project 3 README](./3_marketing_campaign_user_actor/README.md)

**Frequency Capping?**
- [Project 3 README](./3_marketing_campaign_user_actor/README.md#how-it-works)

**Validators?**
- [Project 2 README](./2_hr_approval_slack/README.md#update-validators)

**Setup Issues?**
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md#general-issues)

**API Examples?**
- [QUICK_START.md](./QUICK_START.md)
- Individual project READMEs

**Workflow Coordination?**
- [PATTERNS_EXPLAINED.md](./PATTERNS_EXPLAINED.md#pattern-4-user-actor-shared-state-coordinator)
- [Project 3 README](./3_marketing_campaign_user_actor/README.md)

## 🎓 Learning Objectives

After completing these projects, you will understand:

✅ How to send data TO workflows (Signals)
✅ How to read data FROM workflows (Queries)
✅ How to do both atomically (Updates)
✅ How to coordinate multiple workflows (User Actor)
✅ When to use each pattern
✅ How to scale to millions of workflows
✅ Real-world patterns for production

## 💡 Pro Tips

1. **Start Simple**: Project 1 → Project 2 → Project 3
2. **Use Temporal UI**: Essential for understanding execution
3. **Read PATTERNS_EXPLAINED**: Best conceptual overview
4. **Keep TROUBLESHOOTING Handy**: Save debugging time
5. **Experiment**: Modify code, break things, learn!

## 🔗 External Resources

- [Temporal Documentation](https://docs.temporal.io)
- [Temporal Community](https://community.temporal.io)
- [Python SDK Docs](https://docs.temporal.io/develop/python)
- [Temporal GitHub](https://github.com/temporalio/temporal)

## 📝 Summary

| File | Purpose | Read When |
|------|---------|-----------|
| README.md | Overview | First |
| QUICK_START.md | Fast setup | Want to run quickly |
| PATTERNS_EXPLAINED.md | Concepts | Learning patterns |
| TROUBLESHOOTING.md | Solutions | Having problems |
| INDEX.md | Navigation | Looking for something |
| Project READMEs | Details | Using that project |

---

**Ready to start?** → [QUICK_START.md](./QUICK_START.md)
**Want to learn first?** → [PATTERNS_EXPLAINED.md](./PATTERNS_EXPLAINED.md)
**Having issues?** → [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

Happy learning! 🚀
