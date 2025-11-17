# Single Node Workflow - Modularized Example

This example demonstrates a clean separation of concerns with separate files for workflow definitions, worker, API, and workflow starter.

## Architecture

```
┌─────────────┐
│  Client     │ (start-workflow.ts or API)
└──────┬──────┘
       │ gRPC
       ▼
┌─────────────────┐
│ Temporal Server │ (localhost:7233)
└──────┬──────────┘
       │ gRPC
       ▼
┌─────────────┐
│   Worker    │ (worker.ts)
│             │
│ • Workflows │
│ • Activities│
└─────────────┘
```

## Files

- **`workflow-definitions.ts`** - Workflow and activity definitions (shared)
- **`worker.ts`** - Worker that processes tasks
- **`api.ts`** - Express REST API to start workflows
- **`start-workflow.ts`** - Direct TypeScript starter script
- **`README.md`** - This documentation

## Running the Example

### Prerequisites

1. **Install dependencies** (from MY folder):
   ```bash
   cd ../../
   npm install
   npm install express @types/express
   npm run build
   ```

2. **Start Temporal server**:
   ```bash
   docker compose up -d
   ```

### Option 1: Using the Worker + Direct Starter

**Terminal 1: Start the Worker**
```bash
node dist/0_simple_split/1_single_node/worker.js
```

**Terminal 2: Run the Workflow**
```bash
node dist/0_simple_split/1_single_node/start-workflow.js
```

### Option 2: Using the Worker + REST API

**Terminal 1: Start the Worker**
```bash
node dist/0_simple_split/1_single_node/worker.js
```

**Terminal 2: Start the API**
```bash
node dist/0_simple_split/1_single_node/api.js
```

**Terminal 3: Trigger via HTTP**
```bash
# Start a workflow
curl -X POST http://localhost:8000/workflow/start \
  -H "Content-Type: application/json" \
  -d '{"input_value": 42}'

# Health check
curl http://localhost:8000/health
```

## Key Concepts

### Separation of Concerns

1. **Workflow Definitions** (`workflow-definitions.ts`)
   - Contains business logic
   - Shared between worker and clients
   - Pure, reusable code

2. **Worker** (`worker.ts`)
   - Long-running process
   - Polls for tasks
   - Executes workflows and activities
   - One worker can handle multiple workflow types

3. **API** (`api.ts`)
   - REST interface for clients
   - Starts workflows
   - Queries workflow state
   - Stateless service

4. **Direct Starter** (`start-workflow.ts`)
   - Simple script to start workflows
   - Useful for testing
   - Can be run from command line or cron jobs

### Benefits of This Pattern

- **Scalability**: Workers can be scaled independently
- **Deployment**: API and workers can be deployed separately
- **Testing**: Each component can be tested in isolation
- **Maintainability**: Clear separation makes code easier to understand
- **Flexibility**: Multiple ways to trigger workflows (API, scripts, etc.)

## Workflow Execution Flow

1. **Client** (API or script) sends workflow start request to Temporal server
2. **Temporal Server** queues the workflow task
3. **Worker** polls and picks up the workflow task
4. **Worker** executes the workflow code
5. **Workflow** schedules activity tasks
6. **Worker** picks up and executes activities
7. **Results** flow back through Temporal server to client

## API Endpoints

### `GET /`
Returns API information and available endpoints.

**Response:**
```json
{
  "name": "Single Node Workflow API",
  "version": "1.0.0",
  "endpoints": {
    "start_workflow": "/workflow/start",
    "health": "/health"
  }
}
```

### `GET /health`
Health check endpoint to verify Temporal connectivity.

**Response:**
```json
{
  "status": "healthy",
  "temporal_connected": true
}
```

### `POST /workflow/start`
Start a new workflow instance.

**Request:**
```json
{
  "input_value": 42,
  "workflow_id": "optional-custom-id"
}
```

**Response:**
```json
{
  "workflow_id": "single-node-workflow-...",
  "result": 84,
  "status": "completed"
}
```

## Configuration

All configuration is defined at the top of each file:

```typescript
const TEMPORAL_HOST = 'localhost:7233';
const TASK_QUEUE = '0-simple-single-node-task-queue';
const PORT = 8000; // API only
```

## Production Considerations

1. **Error Handling**: Add proper error handling and retries
2. **Logging**: Use structured logging (Winston, Pino)
3. **Monitoring**: Add metrics and health checks
4. **Security**: Add authentication for API endpoints
5. **Configuration**: Use environment variables
6. **Multiple Workers**: Run multiple worker instances for high availability
7. **Load Balancing**: Use load balancer in front of API instances

## Next Steps

- Try `2_multiple_nodes/` for sequential activity execution
- See `1_basic_split/` for more complex patterns (child workflows, signals)
- Check `2_intermediate/` for production-ready patterns
