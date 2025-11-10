# Project 3: Code Review Pipeline with Multi-Agent Teams

This project demonstrates multi-agent teams using the **supervision pattern**, where a supervisor agent coordinates multiple specialist agents working together on code review tasks.

## Multi-Agent Architecture

```
┌──────────────────┐
│  Code Submission │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│  Supervisor Agent            │ ◄── Coordinates team
│  ┌─────────────────────────┐ │
│  │ Assigns tasks           │ │
│  │ Aggregates findings     │ │
│  │ Resolves conflicts      │ │
│  └─────────────────────────┘ │
└────────┬─────────────────────┘
         │
         ├────────┬────────┬────────┬────────┐
         │        │        │        │        │
         ▼        ▼        ▼        ▼        ▼
    ┌────────┐┌──────┐┌───────┐┌───────┐┌────────┐
    │Security││Perf  ││ Style ││ Test  ││ Doc    │
    │ Agent  ││Agent ││ Agent ││ Agent ││ Agent  │
    └────────┘└──────┘└───────┘└───────┘└────────┘
         │        │        │        │        │
         └────────┴────────┴────────┴────────┘
                       │
                       ▼
               ┌──────────────┐
               │ Aggregated   │
               │ Review Report│
               └──────────────┘
```

## Features

### Supervision Pattern
- **Supervisor Agent**: Orchestrates team of specialists
- **Task Distribution**: Routes work to appropriate agents
- **Result Aggregation**: Combines findings from all agents
- **Conflict Resolution**: Resolves contradictory recommendations

### Specialist Agents

1. **Security Agent** (with E2B sandbox)
   - Scans for vulnerabilities
   - Tests for injection attacks
   - Validates authentication/authorization

2. **Performance Agent** (with E2B)
   - Analyzes algorithmic complexity
   - Runs performance benchmarks
   - Suggests optimizations

3. **Style Agent** (with Academia MCP)
   - Checks coding standards
   - Reviews documentation
   - Validates naming conventions

4. **Test Agent** (with E2B)
   - Writes unit tests
   - Creates integration tests
   - Generates coverage reports

5. **Documentation Agent**
   - Reviews inline comments
   - Checks API documentation
   - Validates README completeness

## Workflow Steps

1. **Code Intake** (Deterministic) - Validate submission
2. **Multi-Agent Review** (Supervision Pattern)
   - Supervisor distributes tasks
   - Agents work in parallel
   - Supervisor aggregates results
3. **Test Execution** (Deterministic) - Run generated tests
4. **Report Generation** (AI Agent with Mem0) - Create final report
5. **Notification** (Deterministic) - Send results

## Key Implementation Details

### Supervisor Agent Pattern

```python
@workflow.defn
class CodeReviewWorkflow:
    @workflow.run
    async def run(self, code_submission):
        # Supervisor coordinates team
        supervisor = Agent(
            name="Review Supervisor",
            instructions="Coordinate specialist agents and aggregate findings",
        )

        # Create specialist agents
        security_agent = Agent(name="Security Specialist", ...)
        perf_agent = Agent(name="Performance Specialist", ...)
        style_agent = Agent(name="Style Specialist", ...)

        # Supervisor assigns and collects
        findings = await supervisor_review(
            supervisor,
            specialists=[security_agent, perf_agent, style_agent],
            code=code_submission
        )

        return findings
```

### Parallel Agent Execution with Coordination

```python
# Execute specialists in parallel
security_future = workflow.execute_activity(security_review, ...)
perf_future = workflow.execute_activity(performance_review, ...)
style_future = workflow.execute_activity(style_review, ...)

# Wait for all to complete
security, perf, style = await workflow.wait_all([
    security_future, perf_future, style_future
])

# Supervisor aggregates
final_report = await workflow.execute_activity(
    aggregate_findings,
    args=[security, perf, style]
)
```

## Running the Example

```bash
# Terminal 1: Start worker
python 3_multi-agents/run_worker.py

# Terminal 2: Execute workflow
python 3_multi-agents/run_workflow.py
```

## Expected Output

```
================================================================================
Code Review Complete
================================================================================

Code: example_api.py (234 lines)

SUPERVISOR SUMMARY
Coordinated 5 specialist agents
Review duration: 45.2 seconds

SECURITY FINDINGS (High Priority)
  ✗ SQL injection vulnerability in line 87
  ✗ Missing input validation in user_login()
  ✓ Authentication properly implemented

PERFORMANCE FINDINGS (Medium Priority)
  ✗ O(n²) algorithm in process_data() - suggest O(n log n)
  ✗ Database query in loop (line 134)
  ✓ Proper caching implemented

STYLE FINDINGS (Low Priority)
  ✗ Inconsistent naming: userId vs user_id
  ✗ Missing docstrings in 5 functions
  ✓ PEP 8 compliance: 94%

TEST COVERAGE
  Generated 23 unit tests
  Coverage: 78% (target: 80%)

  Suggested Additional Tests:
    - Edge case: empty user input
    - Integration: full auth flow
    - Performance: load testing

OVERALL RECOMMENDATION: Address security issues before merge
Confidence: 92%
```

## Next Steps

See **Project 4** for combining all patterns (LLM calls, single agents, multi-agent teams)
