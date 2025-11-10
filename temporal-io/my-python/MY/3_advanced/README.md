# Advanced: Dynamic Workflows

This folder demonstrates **Dynamic Workflows** in Temporal - workflows that are constructed and determined at runtime based on input data and configuration. This is an advanced concept that enables highly flexible, data-driven workflow orchestration.

## What Are Dynamic Workflows?

Dynamic workflows allow you to:

1. **Execute activities by name at runtime** - Determine which activities to run based on configuration
2. **Spawn child workflows dynamically** - Create child workflows based on runtime data
3. **Build workflow execution paths at runtime** - Construct complex workflow logic from configuration
4. **Register handlers dynamically** - Add signal and query handlers based on runtime needs

**Yes, dynamic workflows are absolutely possible in Temporal!** These examples demonstrate multiple approaches to achieve runtime workflow construction.

## Examples

### 1. Dynamic Activity Invocation (`dynamic_activity_invocation.py`)

**Concept**: Execute activities by name at runtime, allowing workflows to determine which activities to run based on input configuration.

**Key Features**:
- Activities executed by string name
- Configurable validation and transformation pipelines
- Runtime-determined activity sequences
- Flexible data processing workflows

**Use Cases**:
- Data validation pipelines with configurable rules
- ETL workflows with runtime-configured transformations
- Multi-stage processing with dynamic step selection
- Plugin-based data processing systems

**Run Example**:
```bash
cd MY/3_advanced
uv run python dynamic_activity_invocation.py
```

**How It Works**:
```python
# Activities are executed by name as strings
result = await workflow.execute_activity(
    "validate_email",  # Activity name as string
    data,
    start_to_close_timeout=timedelta(seconds=10),
)

# Configuration determines which activities to run
config = WorkflowConfig(
    validation_rules=["validate_email", "validate_phone"],
    transformations=["transform_uppercase"],
    enrichment=True,
)
```

### 2. Dynamic Child Workflows (`dynamic_child_workflows.py`)

**Concept**: Spawn child workflows dynamically at runtime based on input data, enabling flexible, data-driven workflow orchestration.

**Key Features**:
- Child workflows selected by data type
- String-based workflow invocation
- Runtime workflow mapping
- Parallel processing of heterogeneous data

**Use Cases**:
- Media processing systems (images, videos, documents)
- Multi-tenant workflows with tenant-specific logic
- Batch processing with item-specific workflows
- Dynamic workflow orchestration based on data type

**Run Example**:
```bash
cd MY/3_advanced
uv run python dynamic_child_workflows.py
```

**How It Works**:
```python
# Map data types to workflow classes
workflow_map = {
    "image": ImageProcessingWorkflow,
    "video": VideoProcessingWorkflow,
    "document": DocumentProcessingWorkflow,
}

# Dynamically select and execute child workflow
workflow_class = workflow_map.get(item.type)
result = await workflow.execute_child_workflow(
    workflow_class.run,
    child_data,
    id=f"child-{item.id}",
)

# Or execute by string name
result = await workflow.execute_child_workflow(
    "ImageProcessingWorkflow",  # String name
    data,
    id="child-workflow-id",
)
```

### 3. Runtime Workflow Builder (`runtime_workflow_builder.py`)

**Concept**: Build complex workflow execution paths at runtime from configuration, enabling completely dynamic workflow construction.

**Key Features**:
- Workflow steps defined as data structures
- Support for sequential, parallel, conditional, and loop execution
- Runtime workflow composition from blueprints
- Configurable workflow logic without code changes

**Use Cases**:
- Business process automation with user-defined workflows
- Low-code/no-code workflow platforms
- A/B testing different workflow paths
- Workflow templates with runtime customization

**Run Example**:
```bash
cd MY/3_advanced
uv run python runtime_workflow_builder.py
```

**How It Works**:
```python
# Define workflow as a blueprint (data structure)
blueprint = WorkflowBlueprint(
    name="Dynamic Pipeline",
    description="Runtime-constructed workflow",
    steps=[
        WorkflowStep(
            id="step1",
            type=StepType.ACTIVITY,
            activity_name="fetch_data",
            params={"source": "database"},
        ),
        WorkflowStep(
            id="step2",
            type=StepType.PARALLEL,
            parallel_steps=[
                WorkflowStep(type=StepType.ACTIVITY, activity_name="transform"),
                WorkflowStep(type=StepType.ACTIVITY, activity_name="enrich"),
            ],
        ),
        WorkflowStep(
            id="step3",
            type=StepType.LOOP,
            loop_count=3,
            loop_steps=[...],
        ),
    ],
    initial_data={"job_id": "job_001"},
)

# Execute the dynamically built workflow
result = await client.execute_workflow(
    RuntimeBuiltWorkflow.run,
    blueprint,
    ...
)
```

### 4. Dynamic Signal and Query Handlers (`dynamic_signals_queries.py`)

**Concept**: Register signal and query handlers dynamically at runtime, allowing workflows to adapt their message handling based on configuration.

**Key Features**:
- Signal handlers registered at runtime
- Query handlers registered at runtime
- Plugin-based workflow architecture
- Configurable workflow interaction patterns

**Use Cases**:
- Multi-tenant workflows with tenant-specific handlers
- Plugin-based workflow systems
- Workflows with runtime-defined APIs
- Configurable workflow control interfaces

**Run Example**:
```bash
cd MY/3_advanced
uv run python dynamic_signals_queries.py
```

**How It Works**:
```python
# Configure signals and queries at runtime
signal_configs = [
    SignalConfig(
        signal_name="update_data",
        handler_type="store",
    ),
    SignalConfig(
        signal_name="complete",
        handler_type="trigger",
    ),
]

query_configs = ["get_status", "get_data", "get_signals"]

# Handlers are registered dynamically in the workflow
@workflow.run
async def run(self, signal_configs, query_configs):
    for config in signal_configs:
        self._register_signal_handler(config)
    for query_name in query_configs:
        self._register_query_handler(query_name)
    ...

# Plugin-based approach
plugin_configs = [
    PluginConfig(
        name="analytics",
        signals=["track_event", "update_metrics"],
        queries=["get_data"],
    ),
    PluginConfig(
        name="notifications",
        signals=["send_email", "send_sms"],
        queries=["get_data"],
    ),
]
```

## Key Concepts

### 1. Activity Invocation by Name

Temporal allows executing activities by string name instead of function reference:

```python
# Static (traditional)
result = await workflow.execute_activity(
    my_activity_function,
    args,
    ...
)

# Dynamic
activity_name = "my_activity_function"  # Determined at runtime
result = await workflow.execute_activity(
    activity_name,  # String name
    args,
    ...
)
```

### 2. Child Workflow Invocation by Name

Similarly, child workflows can be invoked by string name:

```python
# Static
result = await workflow.execute_child_workflow(
    MyChildWorkflow.run,
    args,
    ...
)

# Dynamic
workflow_name = "MyChildWorkflow"  # Determined at runtime
result = await workflow.execute_child_workflow(
    workflow_name,  # String name
    args,
    ...
)
```

### 3. Workflow as Data

Workflows can be represented as data structures and interpreted at runtime:

```python
# Workflow structure as data
workflow_definition = {
    "steps": [
        {"type": "activity", "name": "fetch_data"},
        {"type": "activity", "name": "transform_data"},
        {"type": "parallel", "steps": [...]},
    ]
}

# Interpreter executes the data-driven workflow
for step in workflow_definition["steps"]:
    if step["type"] == "activity":
        await workflow.execute_activity(step["name"], ...)
    elif step["type"] == "parallel":
        await asyncio.gather(...)
```

### 4. Dynamic Handler Registration

Signal and query handlers can be registered dynamically:

```python
# Register handlers based on configuration
for signal_name in config.signals:
    @workflow.signal(name=signal_name)
    def handler(self, data):
        # Handle signal
        ...
    setattr(self, f"_handler_{signal_name}", handler)

for query_name in config.queries:
    @workflow.query(name=query_name)
    def handler(self):
        # Handle query
        ...
    setattr(self, f"_query_{query_name}", handler)
```

## Benefits of Dynamic Workflows

1. **Flexibility**: Workflows can adapt to different scenarios without code changes
2. **Reusability**: Single workflow implementation handles multiple use cases
3. **Configuration-Driven**: Business logic can be changed via configuration
4. **Scalability**: Handle diverse workload patterns with minimal code
5. **Multi-Tenancy**: Support tenant-specific logic without separate workflows
6. **Rapid Development**: Build workflow systems that users can customize

## When to Use Dynamic Workflows

**Use Dynamic Workflows When**:
- Workflow logic varies significantly based on input data
- You need configuration-driven workflow orchestration
- Building workflow platforms or frameworks
- Supporting multi-tenant scenarios with varying logic
- Enabling user-defined workflows

**Avoid Dynamic Workflows When**:
- Workflow logic is static and well-defined
- Type safety and compile-time checking are critical
- Workflow is simple and doesn't need flexibility
- Team prefers explicit, strongly-typed code

## Common Patterns

### Pattern 1: Activity Pipeline Builder
```python
# Define pipeline as list of activity names
pipeline = ["fetch", "validate", "transform", "save"]

# Execute pipeline dynamically
for activity_name in pipeline:
    result = await workflow.execute_activity(activity_name, data)
    data = result  # Pass output to next activity
```

### Pattern 2: Type-Based Child Workflow Dispatch
```python
# Map types to workflows
workflow_map = {
    "type_a": WorkflowA,
    "type_b": WorkflowB,
}

# Dispatch based on type
for item in items:
    workflow_class = workflow_map[item.type]
    await workflow.execute_child_workflow(workflow_class.run, item)
```

### Pattern 3: Conditional Execution Graph
```python
# Build execution graph from config
graph = {
    "step1": {"activity": "fetch", "next": "step2"},
    "step2": {"activity": "validate", "next_on_success": "step3", "next_on_failure": "step4"},
    ...
}

# Execute graph
current_step = "step1"
while current_step:
    step_config = graph[current_step]
    result = await execute_step(step_config)
    current_step = determine_next_step(step_config, result)
```

### Pattern 4: Plugin System
```python
# Load plugins dynamically
plugins = load_plugins_from_config()

# Register plugin handlers
for plugin in plugins:
    for signal in plugin.signals:
        register_signal_handler(f"{plugin.name}_{signal}")
    for query in plugin.queries:
        register_query_handler(f"{plugin.name}_{query}")
```

## Prerequisites

1. Temporal server running on `localhost:7233`
2. Python environment with Temporal SDK installed
3. Understanding of basic Temporal concepts (workflows, activities, signals, queries)

## Running Examples

Each example is self-contained and can be run independently:

```bash
# From the MY/3_advanced directory
cd MY/3_advanced

# Run any example
uv run python dynamic_activity_invocation.py
uv run python dynamic_child_workflows.py
uv run python runtime_workflow_builder.py
uv run python dynamic_signals_queries.py
```

## Learning Path

1. **Start with**: `dynamic_activity_invocation.py` - Learn basic dynamic execution
2. **Then**: `dynamic_child_workflows.py` - Understand dynamic orchestration
3. **Next**: `runtime_workflow_builder.py` - See full workflow construction
4. **Finally**: `dynamic_signals_queries.py` - Master dynamic interaction patterns

## Additional Resources

- [Temporal Documentation](https://docs.temporal.io/)
- [Temporal Python SDK](https://github.com/temporalio/sdk-python)
- [Dynamic Workflows Best Practices](https://docs.temporal.io/workflows)

## Notes

- Dynamic workflows trade type safety for flexibility
- Careful configuration validation is important
- Activity/workflow names must match registered names exactly
- Consider using enums or constants for activity/workflow names
- Test dynamic workflows thoroughly with various configurations
- Document your configuration schemas clearly

## Summary

**Yes, Temporal absolutely supports dynamic workflows!** These examples demonstrate that workflows can be:

1. ✅ Constructed at runtime from configuration
2. ✅ Executed with dynamic activity selection
3. ✅ Orchestrated with dynamic child workflows
4. ✅ Customized with dynamic signal/query handlers

The key is understanding that Temporal allows:
- Activity invocation by string name
- Child workflow invocation by string name
- Conditional logic and loops in workflows
- Dynamic handler registration

This enables building highly flexible, configuration-driven workflow systems that adapt to runtime requirements without code changes.
