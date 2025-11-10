# Multiple Nodes Example

Demonstrates a workflow with multiple activities executed sequentially. This example shows how to build a multi-step workflow with validation, transformation, and persistence logic.

## Architecture

This example separates concerns into distinct components:

- **`workflow_definitions.py`** - Shared workflow and activity definitions
- **`worker.py`** - Worker script that processes workflow tasks
- **`start_workflow.py`** - Python script to start workflow instances
- **`api.py`** - FastAPI REST API to start workflows via HTTP

## Workflow Flow

The workflow executes three sequential activities:

```
Input → [1. Validate] → [2. Transform] → [3. Save] → Result
```

1. **Validate Input** - Checks if the input value is positive
   - If invalid: workflow returns "Input validation failed"
   - If valid: proceeds to transformation

2. **Transform Data** - Applies transformation: `value * 3 + 10`
   - Example: Input `15` → `15 * 3 + 10 = 55`

3. **Save Result** - Saves the transformed value (simulation)
   - Returns: `"Successfully saved value: {transformed_value}"`

## Prerequisites

1. Temporal server running locally on `localhost:7233`
2. Python dependencies installed via `uv sync`

## Usage

### 1. Start the Worker

The worker must be running to process workflow tasks:

```bash
cd MY/0_simple_split/2_multiple_nodes
uv run python worker.py
```

Output:
```
Connected to Temporal at localhost:7233
Worker started on task queue: 0-simple-multiple-nodes-task-queue
Max concurrent activities: 10
Registered activities: validate_input, transform_data, save_result
Press Ctrl+C to stop the worker
```

### 2. Start Workflows

#### Option A: Python Script

Simple script to start workflows:

```bash
uv run python start_workflow.py
```

The script includes two examples:
- Valid input (15) - completes successfully
- Invalid input (-5) - fails validation

**Programmatic usage:**

```python
import asyncio
from start_workflow import start_workflow

# Start with default auto-generated ID
result = asyncio.run(start_workflow(input_value=15))

# Start with custom workflow ID
result = asyncio.run(start_workflow(
    input_value=100,
    workflow_id="my-multi-step-workflow"
))
```

#### Option B: FastAPI REST API

Start the API server (note: different port from single node example):

```bash
uv run python api.py
```

The API will be available at `http://localhost:8001`

**Endpoints:**

1. **Get Workflow Info**
   ```bash
   curl http://localhost:8001/workflow/info
   ```

2. **Health Check**
   ```bash
   curl http://localhost:8001/health
   ```

3. **Start Workflow**

   Valid input:
   ```bash
   curl -X POST http://localhost:8001/workflow/start \
     -H "Content-Type: application/json" \
     -d '{"input_value": 15}'
   ```

   Invalid input (will fail validation):
   ```bash
   curl -X POST http://localhost:8001/workflow/start \
     -H "Content-Type: application/json" \
     -d '{"input_value": -5}'
   ```

   With custom workflow ID:
   ```bash
   curl -X POST http://localhost:8001/workflow/start \
     -H "Content-Type: application/json" \
     -d '{"input_value": 42, "workflow_id": "my-workflow-123"}'
   ```

4. **API Documentation**

   Interactive API docs available at:
   - Swagger UI: `http://localhost:8001/docs`
   - ReDoc: `http://localhost:8001/redoc`

## Configuration

All scripts use the following configuration:

- **Temporal Host**: `localhost:7233`
- **Task Queue**: `0-simple-multiple-nodes-task-queue`
- **Max Concurrent Activities**: 10
- **API Port**: 8001 (different from single node example on 8000)

To modify these, edit the constants at the top of each file.

## Example Execution

### Valid Input Example

Input: `15`

1. **Validation**: `15 > 0` → ✓ Valid
2. **Transformation**: `15 * 3 + 10 = 55`
3. **Save**: `"Successfully saved value: 55"`

Result: `"Successfully saved value: 55"`

### Invalid Input Example

Input: `-5`

1. **Validation**: `-5 > 0` → ✗ Invalid
2. Workflow terminates early

Result: `"Input validation failed"`

## File Structure

```
2_multiple_nodes/
├── workflow_definitions.py   # Workflow and activity definitions
├── worker.py                  # Worker script
├── start_workflow.py          # Python workflow starter
├── api.py                     # FastAPI workflow starter
└── README.md                  # This file
```

## Key Differences from Single Node

1. **Multiple Activities**: Three sequential activities vs. one
2. **Conditional Logic**: Workflow can fail early at validation step
3. **Data Flow**: Each activity passes data to the next
4. **Different Port**: API runs on 8001 to avoid conflicts
5. **More Complex**: Demonstrates realistic multi-step processing

## Development Notes

- The worker must be running before starting workflows
- Each workflow instance needs a unique ID (auto-generated if not specified)
- Activities execute sequentially - each waits for the previous to complete
- Failed validation stops the workflow early
- All components use async/await for non-blocking operations
- Activity logs show detailed execution flow
