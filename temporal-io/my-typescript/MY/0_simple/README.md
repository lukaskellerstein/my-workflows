# 0_simple - Basic Workflow Patterns

This folder contains the simplest possible Temporal workflow examples in TypeScript.

## Important Note About TypeScript Structure

**Unlike Python**, TypeScript Temporal workflows cannot be truly single-file due to the SDK's bundling requirements:
- Workflows run in an isolated, deterministic sandbox
- Activities run in regular Node.js
- The bundler needs to separate these concerns

Therefore, each example uses the **modular approach** found in `0_simple_split` with separate files for clarity and proper isolation.

For truly self-contained single-file examples (like Python), see the **`0_simple_split/`** folder which demonstrates the pattern with full documentation.

## Examples

Each example demonstrates a fundamental workflow pattern:

### 1. Single Node
The simplest possible workflow with a single activity.

**Pattern**: Workflow → Single Activity → Result

**Files**: See `0_simple_split/1_single_node/`

### 2. Multiple Nodes
Sequential execution of multiple activities.

**Pattern**: Workflow → Activity 1 → Activity 2 → Activity 3 → Result

**Files**: See `0_simple_split/2_multiple_nodes/`

### 3. Fan-In Fan-Out
Parallel execution of activities with result aggregation.

**Pattern**:
```
Workflow → [Activity 1, Activity 2, Activity 3] (parallel) → Aggregate → Result
```

###  4. If Condition
Conditional branching in workflows.

**Pattern**:
```
Workflow → Check Condition
           ├─ True: Execute Activity → Result
           └─ False: Skip → Result
```

### 5. Loop
Iteration patterns in workflows.

**Pattern**:
```
Workflow → Loop N times → Execute Activity in each iteration → Collect Results
```

## Recommended Structure (from 0_simple_split)

For production code and better learning, use the modular structure:

```
example/
├── workflows.ts          # Workflow definitions (deterministic code)
├── activities.ts         # Activity implementations (side effects)
├── worker.ts             # Worker process
├── client.ts             # Workflow starter/client
└── README.md             # Documentation
```

## Prerequisites

1. **Install dependencies** (from MY folder):
   ```bash
   cd ..
   npm install
   ```

2. **Start Temporal server** (using Docker):
   ```bash
   docker compose up -d
   ```

3. **Verify Temporal is running**:
   - Web UI: http://localhost:8080
   - gRPC: localhost:7233

## Key Concepts

### Workflows
- **Deterministic** - No side effects, must be reproducible
- **Durable** - Automatically persisted and can be resumed
- **Versioned** - Can evolve over time
- **Isolated** - Run in a sandbox, limited imports allowed

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
- ❌ Cannot import `@temporalio/client`, `@temporalio/worker`, `@temporalio/activity`

### Activities
Activities are the units of work that can fail and be retried. They typically:
- Perform I/O operations
- Call external services
- Access databases
- Have retry policies

### Workers
Workers host and execute workflow and activity code. They:
- Poll the Temporal server for tasks
- Execute workflows and activities
- Report results back to the server

## Common Patterns

### 1. Execute Activity
```typescript
const result = await proxyActivities<typeof activities>({
  startToCloseTimeout: '10 seconds',
}).myActivity(input);
```

### 2. Parallel Execution
```typescript
const results = await Promise.all([
  activity1(input),
  activity2(input),
  activity3(input),
]);
```

### 3. Conditional Logic
```typescript
const condition = await checkActivity(input);
if (condition) {
  return await mainPath(input);
} else {
  return await alternatePath(input);
}
```

### 4. Loops
```typescript
const results = [];
for (let i = 0; i < iterations; i++) {
  const result = await processActivity(i);
  results.push(result);
}
```

## Why Can't TypeScript Be Single-File Like Python?

**Python Temporal SDK**:
- Uses decorators (`@activity.defn`, `@workflow.defn`)
- Runtime imports work fine
- Single-file examples are possible

**TypeScript Temporal SDK**:
- Uses Webpack bundling for workflow code
- Workflow code is isolated in a V8 sandbox
- Bundler strips out non-workflow imports automatically
- Mixing workflow + activity + client code in one file breaks the bundler

**Solution**: Use the modular structure in `0_simple_split/` which provides:
- Clean separation of concerns
- Proper TypeScript typing
- Production-ready structure
- Easy to test and maintain

## Next Steps

Once you're comfortable with these basic patterns, move on to:
- `0_simple_split/` - **START HERE** for properly structured examples with full documentation
- `1_basic/` - Child workflows and human-in-the-loop patterns
- `2_intermediate/` - Real-world production patterns with signals and queries
