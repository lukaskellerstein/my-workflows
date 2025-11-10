# Project 3: Code Review Pipeline with Multi-Agent Teams

This project demonstrates a sophisticated code review system using a team of specialized AI agents working together to analyze, test, and improve submitted code using the supervision pattern.

## Overview

The workflow orchestrates multiple specialized AI agents that work together to provide comprehensive code reviews:

- **Security Agent** - Scans for vulnerabilities using E2B sandbox
- **Performance Agent** - Analyzes complexity and runs benchmarks
- **Style Agent** - Reviews code style and documentation with Academia MCP
- **Test Agent** - Generates and executes test suites
- **Supervisor Agent** - Coordinates the team and synthesizes findings

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           Code Review Workflow (Temporal)           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Validate Submission (Deterministic)            │
│  2. Multi-Agent Review (Supervision Pattern)       │
│  3. Execute Tests (Deterministic)                  │
│  4. Generate Report (AI Agent + Mem0)              │
│  5. Send Notifications (Deterministic)             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Project Structure

```
p3_multi_agents_new/
├── __init__.py
├── run_worker.py            # Worker startup script
├── run_workflow.py          # Workflow execution script
├── main_workflow/           # Main workflow package
│   ├── __init__.py
│   ├── workflow.py          # Temporal workflow definition
│   └── activities/          # Individual activity modules
│       ├── __init__.py
│       ├── validate_code_submission.py
│       ├── multi_agent_code_review.py
│       ├── execute_generated_tests.py
│       ├── generate_review_report.py
│       └── send_notifications.py
├── agents/                  # AI agent implementations
│   ├── __init__.py
│   └── code_review_team.py  # Multi-agent team coordination
├── models/                  # Project-specific models
│   └── __init__.py
├── shared/                  # Shared utilities
│   ├── __init__.py
│   ├── models.py            # Pydantic models
│   ├── config.py            # Configuration management
│   ├── sdk_wrapper.py       # Claude SDK wrapper
│   └── mcp_config.py        # MCP server configurations
├── tests/                   # Test suite
│   └── __init__.py
├── pyproject.toml           # Project dependencies
├── .env                     # Environment variables
├── .gitignore               # Git ignore patterns
└── README.md                # This file
```

## Prerequisites

1. **Python 3.11+**
2. **uv** package manager
3. **Temporal Server** running locally
4. **MongoDB** (optional, for extended features)
5. **MCP Servers**:
   - E2B (for code execution)
   - Academia (for coding standards)
   - Mem0 (for memory/context)

## Installation

1. Create and activate virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
uv sync
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

## Configuration

Edit `.env` file with your settings:

```env
# Temporal
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default

# MCP Services
TAVILY_API_KEY=your_tavily_key
E2B_API_KEY=your_e2b_key
OPENMEMORY_API_KEY=your_mem0_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# MongoDB
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/temporal_claude_sdk

# Settings
LOG_LEVEL=INFO
MAX_RETRIES=3
TIMEOUT_SECONDS=300
```

## Usage

### Start Temporal Server

If not already running:
```bash
temporal server start-dev
```

### Run the Worker

In one terminal:
```bash
python run_worker.py
```

### Execute Workflow

In another terminal:
```bash
python run_workflow.py
```

## Workflow Activities

### 1. Code Intake (Deterministic)
- Validates file format
- Checks code length constraints
- Verifies metadata requirements

### 2. Multi-Agent Code Review (Supervision Pattern)

The supervisor coordinates specialist agents:

**Security Agent** (E2B):
- Scans for vulnerabilities
- Tests for injection attacks
- Validates authentication logic

**Performance Agent** (E2B):
- Analyzes algorithmic complexity
- Runs performance benchmarks
- Suggests optimizations

**Style Agent** (Academia):
- Checks coding standards
- Reviews documentation
- Validates naming conventions

**Test Agent** (E2B):
- Writes unit tests
- Creates integration tests
- Generates coverage reports

### 3. Test Execution (Deterministic)
- Runs generated test suites
- Executes benchmarks
- Compiles results

### 4. Report Generation (AI + Mem0)
- Synthesizes all findings
- Recalls similar past reviews
- Creates actionable recommendations

### 5. Notifications (Deterministic)
- Formats report
- Sends to stakeholders
- Archives artifacts

## Agent Team Pattern

This project uses the **Supervision Pattern** from Claude Agent SDK:

```python
team = SupervisorTeam(
    supervisor_name="tech-lead",
    supervisor_description="Coordinates code review team",
    team_agents={
        "security-expert": AgentDefinition(...),
        "performance-expert": AgentDefinition(...),
        "style-expert": AgentDefinition(...),
        "test-expert": AgentDefinition(...),
    },
    mcp_servers=["e2b", "academia"],
)

result = await team.execute(task="Review this code...")
```

## Key Features

- **Temporal Workflows**: Reliable orchestration with retries and error handling
- **Multi-Agent Coordination**: Specialized agents working together
- **MCP Tool Integration**: E2B sandboxes, Academia research, Mem0 memory
- **Comprehensive Testing**: Automated test generation and execution
- **Historical Context**: Mem0 remembers past reviews for better insights

## Example Output

```
============================================================
CODE REVIEW COMPLETED
============================================================
Submission ID: sub-20250104-123456
Overall Score: 72/100
Security Findings: 3
  - Critical Issues: 1
Performance Bottlenecks: 2
Style Issues: 5
Test Coverage: 85%
Test Results: 11/12 passed

Priority Issues:
  - SQL injection vulnerability in authenticate_user()
  - O(n^2) complexity in process_user_data()
  - Missing type hints in calculate_total()

Recommendations:
  - Use parameterized queries for database access
  - Implement more efficient sorting algorithm
  - Add comprehensive type annotations
============================================================
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality

This project follows clean code principles:
- Single Responsibility
- DRY (Don't Repeat Yourself)
- Clear naming conventions
- Comprehensive error handling

## Troubleshooting

### Common Issues

1. **MCP Server Connection Failed**
   - Check API keys in `.env`
   - Verify MCP servers are accessible
   - Check logs for specific errors

2. **Temporal Connection Failed**
   - Ensure Temporal server is running
   - Verify `TEMPORAL_HOST` in `.env`
   - Check namespace configuration

3. **Agent Timeout**
   - Increase `TIMEOUT_SECONDS` in `.env`
   - Check network connectivity
   - Review code complexity

## License

MIT

## References

- [Claude Agent SDK Documentation](https://github.com/anthropics/claude-agent-sdk)
- [Temporal.io Documentation](https://docs.temporal.io)
- [E2B Documentation](https://e2b.dev/docs)
- [Mem0 Documentation](https://docs.mem0.ai)
