# Simple Split Example

Demonstrates a clean separation between worker and workflow execution with a simple single-node workflow.

## Architecture

This example separates concerns into distinct components:

- **`workflow_definitions.py`** - Shared workflow and activity definitions
- **`worker.py`** - Worker script that processes workflow tasks
- **`start_workflow.py`** - Python script to start workflow instances
- **`api.py`** - FastAPI REST API to start workflows via HTTP

## Prerequisites

1. Temporal server running locally on `localhost:7233`
2. Python dependencies installed via `uv sync`

## Usage

### 1. Start the Worker

The worker must be running to process workflow tasks:

```bash
uv run python worker.py
```

Output:
```
Connected to Temporal at localhost:7233
Worker started on task queue: 0-simple-single-node-task-queue
Max concurrent activities: 5
Press Ctrl+C to stop the worker
```

### 2. Start Workflows

#### Option A: Python Script

Simple script to start a workflow:

```bash
uv run python start_workflow.py
```

You can also import and use it programmatically:

```python
import asyncio
from start_workflow import start_workflow

# Start with default auto-generated ID
result = asyncio.run(start_workflow(input_value=42))

# Start with custom workflow ID
result = asyncio.run(start_workflow(
    input_value=100,
    workflow_id="my-custom-workflow-id"
))
```

#### Option B: FastAPI REST API

Start the API server:

```bash
uv run python api.py
```

The API will be available at `http://localhost:8000`

**Endpoints:**

1. **Health Check**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Start Workflow**
   ```bash
   curl -X POST http://localhost:8000/workflow/start \
     -H "Content-Type: application/json" \
     -d '{"input_value": 42}'
   ```

   With custom workflow ID:
   ```bash
   curl -X POST http://localhost:8000/workflow/start \
     -H "Content-Type: application/json" \
     -d '{"input_value": 42, "workflow_id": "my-workflow-123"}'
   ```

3. **API Documentation**

   Interactive API docs available at:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## Configuration

All scripts use the following configuration:

- **Temporal Host**: `localhost:7233`
- **Task Queue**: `0-simple-single-node-task-queue`
- **Max Concurrent Activities**: 5

To modify these, edit the constants at the top of each file.

## Workflow Details

The `SingleNodeWorkflow` executes a single activity that:
1. Takes an integer input
2. Doubles the value
3. Returns the result

Example:
- Input: `42`
- Output: `84`

## File Structure

```
0_simple_split/
├── workflow_definitions.py   # Workflow and activity definitions
├── worker.py                  # Worker script
├── start_workflow.py          # Python workflow starter
├── api.py                     # FastAPI workflow starter
└── README.md                  # This file
```

## Development Notes

- The worker must be running before starting workflows
- Each workflow instance needs a unique ID (auto-generated if not specified)
- The API waits for workflow completion before returning the result
- All components use async/await for non-blocking operations
