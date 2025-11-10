# Project 3: Code Review Pipeline (Multi-Agent)

## Overview

A code review workflow using a team of specialized AI agents in a supervision pattern.

## Architecture

```
Supervisor Agent
    ├──► Security Agent (E2B sandbox)
    ├──► Performance Agent (E2B sandbox)
    ├──► Style Agent (Academia MCP for best practices)
    └──► Test Agent (E2B sandbox)
```

## Status

This is a stub implementation. The full version would include:

1. **Supervisor Agent**: Coordinates specialist agents
2. **Security Agent**: Scans for vulnerabilities using E2B
3. **Performance Agent**: Analyzes complexity and performance
4. **Style Agent**: Reviews coding standards
5. **Test Agent**: Generates and runs tests

## Implementation Notes

Full implementation would use:
- LangGraph for multi-agent orchestration
- Supervision pattern for agent coordination
- E2B MCP for code execution
- Academia MCP for best practices lookup

## To Implement

Run the following to see the structure:

```bash
cd 3_multi-agents
python main.py  # Would execute multi-agent code review
```
