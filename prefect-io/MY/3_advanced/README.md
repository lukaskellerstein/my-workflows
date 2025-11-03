# 3. Advanced: Dynamic Workflows

This folder demonstrates Prefect's powerful **dynamic workflow** capabilities - the ability to construct and modify workflow structure at runtime based on data, configuration, and conditions.

## What are Dynamic Workflows?

Dynamic workflows are workflows where:
- **Structure is determined at runtime** (not hardcoded at design time)
- **Number of tasks varies** based on input data
- **Execution paths change** based on conditions
- **Workflow DAG is constructed** from configuration or metadata

This is fundamentally different from static workflows where the structure is fixed.

## Is it Possible? YES!

Prefect fully supports dynamic workflow construction through several mechanisms:

1. **Dynamic Task Mapping** - `.map()` with runtime data
2. **Conditional Execution** - Runtime branching logic
3. **Dynamic Subflows** - Creating and invoking flows at runtime
4. **Data-Driven DAGs** - Building entire workflows from configuration

## Examples Overview

### 1. Dynamic Task Mapping (`01_dynamic_task_mapping.py`)

Demonstrates how to create variable numbers of parallel tasks based on runtime data.

**Key Patterns:**
- **Basic Mapping**: Process unknown number of files discovered at runtime
- **Nested Mapping**: Map over dynamically discovered API endpoints
- **Dynamic Unmapping**: Flatten variable-length results
- **Dynamic Batching**: Determine batch size at runtime

**Real-World Use Cases:**
- Processing files in a directory (unknown count until runtime)
- Calling discovered API endpoints (different services have different endpoints)
- Processing variable-length lists from database queries
- Adaptive batch sizing based on data volume

**Example:**
```python
# Discover files at runtime
discovered_files = os.listdir(directory)

# Create one task per file (number unknown at design time)
results = analyze_file.map(discovered_files)
```

### 2. Conditional Branching (`02_conditional_branching.py`)

Demonstrates dynamic execution paths based on runtime conditions.

**Key Patterns:**
- **Quality-Based Routing**: Different processing paths for high/medium/low quality data
- **Multi-Stage Conditionals**: Complex branching with multiple decision points
- **Feature Flag Branching**: Dynamic feature enablement per user

**Real-World Use Cases:**
- Data quality-based processing (fast track vs. remediation)
- Transaction approval workflows (normal vs. manual review)
- A/B testing and feature rollouts
- Error handling and retry strategies

**Example:**
```python
# Assess quality at runtime
quality = assess_data_quality(data)

# Different paths based on runtime condition
if quality == DataQuality.HIGH:
    result = fast_track_processing(data)
elif quality == DataQuality.LOW:
    result = remediation_processing(data)
else:
    result = standard_processing(data)
```

### 3. Dynamic Subflows (`03_dynamic_subflows.py`)

Demonstrates creating and invoking flows at runtime.

**Key Patterns:**
- **Runtime Flow Selection**: Choose which subflow to invoke based on data
- **Dynamic Flow Generation**: Create flow definitions at runtime
- **Pipeline Composition**: Assemble complex workflows from reusable components
- **Parallel Subflows**: Execute multiple subflow instances concurrently

**Real-World Use Cases:**
- ETL pipelines with different transformations per data type
- Plugin-style architectures with runtime-selected processors
- Multi-region processing with region-specific logic
- Configurable data processing pipelines

**Example:**
```python
# Define different transform flows
transform_flows = {
    "csv": transform_csv_flow,
    "json": transform_json_flow,
    "xml": transform_xml_flow
}

# Select and invoke at runtime
transform_flow = transform_flows[source_type]
result = transform_flow(data)
```

### 4. Data-Driven Pipelines (`04_data_driven_pipelines.py`)

The most advanced pattern - constructing entire workflow structures from data/config.

**Key Patterns:**
- **Schema-Driven Processing**: Build pipeline from data schema
- **DAG from Configuration**: Construct complete workflow DAG from config
- **Dependency Resolution**: Execute steps in computed dependency order
- **Adaptive Pipelines**: Change strategy based on runtime metrics

**Real-World Use Cases:**
- Generic ETL frameworks driven by metadata
- Multi-tenant systems with per-tenant workflows
- Configurable data validation and transformation
- Self-optimizing pipelines that adapt to performance

**Example:**
```python
# Schema defines the pipeline structure
schema = [
    {
        "name": "email",
        "validations": ["not_null", "email_format"],
        "transformations": ["trim", "lowercase"]
    },
    # ... more fields
]

# Pipeline is constructed from schema at runtime
for field in schema:
    # Create validation tasks dynamically
    for validation in field["validations"]:
        validate_field(field["name"], validation, data)

    # Create transformation tasks dynamically
    for transform in field["transformations"]:
        transform_field(field["name"], transform, data)
```

## Comparison: Static vs. Dynamic Workflows

### Static Workflow (Fixed Structure)
```python
@flow
def static_workflow():
    # Always processes exactly 3 files
    result1 = process_file("file1.txt")
    result2 = process_file("file2.txt")
    result3 = process_file("file3.txt")
    return [result1, result2, result3]
```

### Dynamic Workflow (Runtime Structure)
```python
@flow
def dynamic_workflow(directory):
    # Processes however many files exist
    files = discover_files(directory)  # Could be 0, 10, 1000...
    results = process_file.map(files)   # Creates N tasks at runtime
    return results
```

## When to Use Dynamic Workflows

✅ **Use Dynamic Workflows When:**
- Number of tasks unknown until runtime (e.g., processing directory listings)
- Workflow structure depends on data (e.g., schema-driven pipelines)
- Need different processing paths based on conditions (e.g., quality routing)
- Building reusable, configurable pipelines (e.g., multi-tenant systems)
- Workflow needs to adapt to runtime metrics (e.g., performance-based strategies)

❌ **Use Static Workflows When:**
- Structure is always the same
- Number of steps is fixed and known
- Simpler to understand and maintain
- Performance is critical (less overhead)

## Advanced Techniques

### 1. Nested Dynamic Mapping

Creating multiple levels of parallelism:

```python
for service in services:
    endpoints = discover_endpoints(service)  # Unknown count
    results = call_endpoint.map([service] * len(endpoints), endpoints)
```

### 2. Dynamic Dependency Resolution

Building execution order at runtime:

```python
# Execute steps in dependency order
while remaining_steps:
    for step in remaining_steps:
        if all_dependencies_satisfied(step):
            execute_step(step)
            completed_steps.add(step)
```

### 3. Runtime Flow Factory

Generating flow definitions programmatically:

```python
def create_processing_flow(flow_name, processing_type):
    @flow(name=flow_name)
    def dynamic_flow(data):
        # Logic based on processing_type
        return process(data, processing_type)

    return dynamic_flow

# Create and execute at runtime
my_flow = create_processing_flow("Custom Flow", "aggregate")
result = my_flow(data)
```

### 4. Adaptive Workflows

Workflows that modify their behavior based on metrics:

```python
strategy = "standard"

for batch in batches:
    result = process_batch(batch, strategy)

    # Analyze and adapt
    if performance_is_low(result):
        strategy = "optimized"
```

## Running the Examples

Each file is standalone and can be run independently:

```bash
# Run individual examples
python 01_dynamic_task_mapping.py
python 02_conditional_branching.py
python 03_dynamic_subflows.py
python 04_data_driven_pipelines.py
```

Each example includes:
- Multiple patterns demonstrating different aspects
- Comprehensive demo that runs all patterns
- Detailed logging showing what's happening at runtime

## Key Takeaways

1. **Prefect FULLY supports dynamic workflows** - you can construct any workflow structure at runtime

2. **Multiple mechanisms available**:
   - `.map()` for dynamic parallelism
   - Python conditionals for branching
   - Flow invocation for dynamic subflows
   - Configuration-driven construction for complex DAGs

3. **Real production value**:
   - Process variable data volumes
   - Build reusable, configurable pipelines
   - Implement adaptive processing strategies
   - Create multi-tenant systems

4. **Prefect visualizes dynamic workflows**:
   - The UI shows the actual runtime structure
   - Can see how many tasks were created
   - Track which paths were taken

## Best Practices

1. **Use `.map()` for homogeneous parallel tasks**
   - When you need to do the same operation on multiple items

2. **Use conditionals for heterogeneous paths**
   - When different items need completely different processing

3. **Use subflows for complex logic reuse**
   - When you have distinct processing pipelines to choose from

4. **Use configuration-driven for maximum flexibility**
   - When building generic frameworks or multi-tenant systems

5. **Consider performance implications**
   - Dynamic workflows have slight overhead
   - But the flexibility usually outweighs the cost

## Further Exploration

These examples can be combined and extended:

- Add dynamic retries based on error types
- Implement circuit breakers that change workflow paths
- Create self-healing workflows that route around failures
- Build workflows that optimize themselves over time
- Develop frameworks where users define workflows via config/UI

The possibilities are endless with Prefect's dynamic workflow capabilities!
