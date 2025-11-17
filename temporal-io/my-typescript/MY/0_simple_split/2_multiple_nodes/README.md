# Multiple Nodes Example

Demonstrates a workflow with multiple activities executed sequentially. This example shows how to build a multi-step workflow with validation, transformation, and persistence logic.

## Architecture

This example separates concerns into distinct components:

- **`activities.ts`** - Activity definitions
- **`workflow-definitions.ts`** - Workflow orchestration logic
- **`worker.ts`** - Worker script that processes workflow tasks
- **`start-workflow.ts`** - Script to start workflow instances
- **`api.ts`** - Express REST API to start workflows via HTTP

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
2. Node.js and npm installed
3. Dependencies installed via `npm install`

## Usage

### 1. Start the Worker

The worker must be running to process workflow tasks:

```bash
cd my-typescript/MY/0_simple_split/2_multiple_nodes
npm run worker
```

Output:
```
Connected to Temporal at localhost:7233
Worker started on task queue: 0-simple-multiple-nodes-task-queue
Registered activities: validateInput, transformData, saveResult
Press Ctrl+C to stop the worker
```

### 2. Start Workflows

#### Option A: Node Script

Simple script to start workflows:

```bash
npm run start-workflow
```

The script includes two examples:
- Valid input (15) - completes successfully
- Invalid input (-5) - fails validation

**Programmatic usage:**

```typescript
import { startWorkflow } from './start-workflow.js';

// Start with default auto-generated ID
const result = await startWorkflow(15);

// Start with custom workflow ID
const result = await startWorkflow(100, 'my-multi-step-workflow');
```

#### Option B: Express REST API

Start the API server (note: different port from single node example):

```bash
npm run api
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

## Configuration

All scripts use the following configuration:

- **Temporal Host**: `localhost:7233`
- **Task Queue**: `0-simple-multiple-nodes-task-queue`
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
├── activities.ts           # Activity definitions
├── workflow-definitions.ts # Workflow orchestration logic
├── worker.ts              # Worker script
├── start-workflow.ts      # Workflow starter script
├── api.ts                 # Express API workflow starter
└── README.md              # This file
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
- Workflows must be deterministic (no side effects in workflow code)
