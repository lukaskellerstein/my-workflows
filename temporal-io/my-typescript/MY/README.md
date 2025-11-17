# Temporal TypeScript Examples

This repository contains a comprehensive set of Temporal workflow examples in TypeScript, organized by complexity and use case.

## Prerequisites

1. **Node.js** >= 18.0.0
2. **Temporal Server** running locally

### Install Dependencies

```bash
npm install
```

### Start Temporal Server

Using Docker:
```bash
docker compose up -d
```

Verify it's running:
- Web UI: http://localhost:8080
- gRPC endpoint: localhost:7233

### Build the Project

```bash
npm run build
```

## Project Structure

```
MY/
├── 0_simple/              # Basic workflow patterns (single files)
├── 0_simple_split/        # Modularized basic examples
├── 1_basic/               # Child workflows, human-in-loop
├── 1_basic_split/         # Modularized composition patterns
├── 2_intermediate/        # Production patterns with signals/queries
├── 3_advanced/            # Dynamic workflows and advanced patterns
├── 5_AI/                  # LLM and AI integration examples
├── 15_k8s/                # Kubernetes deployment examples
├── package.json           # Dependencies and scripts
├── tsconfig.json          # TypeScript configuration
└── README.md              # This file
```

## Learning Path

### Level 0: Simple Patterns (`0_simple/`)

Start here if you're new to Temporal. Single-file examples demonstrating fundamental patterns:

1. **Single Node** - One workflow, one activity
2. **Multiple Nodes** - Sequential activity execution
3. **Fan-In Fan-Out** - Parallel execution
4. **If Condition** - Conditional branching
5. **Loop** - Iteration patterns

**Run Example:**
```bash
npm run build
node dist/0_simple/single_node.js
```

### Level 0.5: Modularized Simple (`0_simple_split/`)

Same patterns as above, but with proper separation of concerns:
- `workflow-definitions.ts` - Shared definitions
- `worker.ts` - Worker process
- `api.ts` - REST API (Express)
- `start-workflow.ts` - Direct starter script

**Benefits:**
- Scalable architecture
- Independent deployment
- Easier testing
- Production-ready structure

**Run Example:**
```bash
# Terminal 1: Start worker
node dist/0_simple_split/1_single_node/worker.js

# Terminal 2: Start workflow
node dist/0_simple_split/1_single_node/start-workflow.js

# OR use the API
# Terminal 2: Start API
node dist/0_simple_split/1_single_node/api.js

# Terminal 3: Trigger via HTTP
curl -X POST http://localhost:8000/workflow/start \
  -H "Content-Type: application/json" \
  -d '{"input_value": 42}'
```

### Level 1: Basic Composition (`1_basic/` and `1_basic_split/`)

Learn workflow composition patterns:
- **Child Workflows** - Parent-child workflow relationships
- **Human-in-Loop** - Signals and approval workflows

### Level 2: Intermediate Patterns (`2_intermediate/`)

Production-ready patterns for real-world applications:
- **E-commerce Order Processing** - Complete order workflow with compensation
- **HR Approval with Slack** - Human approval via Slack integration
- **Marketing Campaign** - User actor pattern

**Key Features:**
- Signals for external input
- Queries for state inspection
- Retry policies
- Compensation logic
- State management

### Level 3: Advanced Patterns (`3_advanced/`)

Advanced runtime techniques:
- Dynamic activity invocation
- Dynamic child workflows
- Dynamic signals and queries
- Runtime workflow builder

### Level 5: AI Integration (`5_AI/`)

Integrating LLMs and AI agents:
- Simple LLM calls
- AI agents with tools
- ReAct (Reasoning + Acting) pattern

### Level 15: Kubernetes (`15_k8s/`)

Deploying Temporal workflows to Kubernetes:
- Starter applications
- Worker deployments
- Scaling strategies

## Common Commands

### Build
```bash
npm run build              # Compile TypeScript
npm run build.watch        # Watch mode for development
```

### Linting and Formatting
```bash
npm run lint               # Check code quality
npm run format             # Format code with Prettier
```

## Key Concepts

### Workflows
- **Deterministic** - No side effects, must be reproducible
- **Durable** - Automatically persisted and can be resumed
- **Versioned** - Can evolve over time

**Do's:**
- ✅ Call activities for I/O operations
- ✅ Use workflow.sleep() for delays
- ✅ Use workflow signals for external input
- ✅ Use workflow queries for state inspection

**Don'ts:**
- ❌ No direct I/O in workflow code
- ❌ No random number generation (use activities)
- ❌ No Date.now() (use workflow.now())
- ❌ No non-deterministic operations

### Activities
- **Retryable** - Automatically retried on failure
- **Side Effects** - Can perform I/O, call APIs, access databases
- **Idempotent** - Should be safe to retry

**Good for:**
- ✅ Database operations
- ✅ API calls
- ✅ File I/O
- ✅ External service integration
- ✅ Non-deterministic operations

### Workers
- **Long-running** processes
- **Poll** Temporal server for tasks
- **Execute** workflows and activities
- **Scalable** - Can run multiple instances

### Signals
- **External input** to running workflows
- **Async** - Don't wait for response
- **Multiple** signals can be sent to same workflow

### Queries
- **Read** workflow state
- **Sync** - Return response immediately
- **Non-mutating** - Don't change workflow state

## Architecture Patterns

### Pattern 1: Monolithic (0_simple/)
```
┌─────────────────────────┐
│   Single Process        │
│  ┌──────────────────┐   │
│  │    Client        │   │
│  ├──────────────────┤   │
│  │    Worker        │   │
│  ├──────────────────┤   │
│  │    Workflows     │   │
│  │    Activities    │   │
│  └──────────────────┘   │
└─────────────────────────┘
```

### Pattern 2: Separated (0_simple_split/)
```
┌──────────┐    ┌─────────────────┐    ┌──────────┐
│  Client  │───▶│ Temporal Server │◀───│  Worker  │
│  (API)   │    └─────────────────┘    │          │
└──────────┘                            │ Workflows│
                                        │ Activities│
                                        └──────────┘
```

### Pattern 3: Multi-Service (2_intermediate/)
```
┌──────────┐         ┌─────────────────┐         ┌──────────┐
│   API    │────────▶│ Temporal Server │◀────────│ Worker 1 │
└──────────┘         └─────────────────┘         └──────────┘
                              ▲                   ┌──────────┐
┌──────────┐                  └───────────────────│ Worker 2 │
│  Script  │                                      └──────────┘
└──────────┘
```

## Development Workflow

1. **Define** your workflow and activities in `workflow-definitions.ts`
2. **Create** a worker in `worker.ts`
3. **Build** the project: `npm run build`
4. **Start** the worker: `node dist/.../worker.js`
5. **Trigger** workflows via API or scripts

## Temporal SDK Packages

- `@temporalio/workflow` - Workflow definitions (runs in isolated sandbox)
- `@temporalio/activity` - Activity definitions (runs in Node.js)
- `@temporalio/worker` - Worker implementation
- `@temporalio/client` - Client to start/query workflows

## Best Practices

1. **Keep workflows deterministic** - All side effects in activities
2. **Use activities for I/O** - Database, API calls, file operations
3. **Set timeouts** - Always configure activity timeouts
4. **Handle errors** - Use try/catch and retry policies
5. **Version workflows** - Plan for workflow evolution
6. **Monitor workflows** - Use Temporal Web UI
7. **Test thoroughly** - Unit test activities, integration test workflows
8. **Scale workers** - Run multiple worker instances for HA

## Troubleshooting

### Workflow not executing
- ✓ Check Temporal server is running
- ✓ Verify worker is started and polling correct task queue
- ✓ Check worker has workflow registered
- ✓ Confirm task queue names match

### Activity timing out
- ✓ Increase `startToCloseTimeout`
- ✓ Check activity is registered in worker
- ✓ Verify activity code doesn't hang
- ✓ Check network connectivity

### Worker crashing
- ✓ Check activity code for unhandled exceptions
- ✓ Verify all dependencies are installed
- ✓ Check TypeScript compilation succeeded
- ✓ Review worker logs for errors

## Resources

- **Temporal Docs**: https://docs.temporal.io
- **TypeScript SDK**: https://typescript.temporal.io
- **Samples**: https://github.com/temporalio/samples-typescript
- **Temporal Web UI**: http://localhost:8080 (when running locally)

## Next Steps

1. Start with `0_simple/single_node.ts` to understand the basics
2. Move to `0_simple_split/1_single_node/` for modularized structure
3. Explore `2_intermediate/` for production patterns
4. Check out `MY_PROJECTS/` for complex real-world examples

Happy workflow building! 🚀
