# 2_visualization - Workflow Visualization

This folder demonstrates how to visualize Prefect workflows using both programmatic and UI-based approaches.

## Prefect Visualization Approaches

Prefect provides two main ways to visualize workflows:

### 1. Programmatic Visualization (`flow.visualize()`)
Static diagram generation using Graphviz during development.

### 2. UI-Based Visualization
Real-time, interactive visualization in the Prefect UI showing actual execution.

## Examples

### 1. Basic Visualization (`01_basic_visualization.py`)
Demonstrates `flow.visualize()` for static diagram generation.

**Demonstrates:**
- Simple linear flows
- Branching flows (conditional logic)
- Parallel flows (independent tasks)
- Multi-level dependencies

**Requirements:**
```bash
# Install system graphviz
sudo apt-get install graphviz  # Linux
brew install graphviz          # Mac

# Install Python package
pip install graphviz
```

**Usage:**
```python
@flow
def my_flow():
    result1 = task_a()
    result2 = task_b(result1)
    return result2

# Generate visualization
my_flow.visualize()
```

**Run:**
```bash
python 01_basic_visualization.py
```

**What You'll See:**
- PNG diagrams showing task dependencies
- Flow execution structure
- Data flow between tasks

### 2. UI Visualization (`02_ui_visualization.py`)
Demonstrates real-time visualization in the Prefect UI.

**Demonstrates:**
- Sequential execution visualization
- Parallel task execution
- Complex multi-pattern workflows
- Real-time state updates

**Setup:**
```bash
# Terminal 1: Start Prefect server
prefect server start

# Terminal 2: Run examples
python 02_ui_visualization.py

# Browser: Open Prefect UI
# http://localhost:4200
```

**Run:**
```bash
python 02_ui_visualization.py
```

**What You'll See in the UI:**
- Interactive workflow graph
- Real-time task state changes
- Execution timeline
- Task logs and details
- Artifacts and outputs

## Comparison: flow.visualize() vs UI

| Feature | flow.visualize() | Prefect UI |
|---------|------------------|------------|
| **When** | Development/documentation | Runtime execution |
| **Type** | Static diagram | Real-time interactive |
| **Execution** | Runs flow to capture dependencies | Shows actual runtime execution |
| **Updates** | Single static image | Updates as flow runs |
| **Interaction** | View only | Click to explore details |
| **States** | Not shown | Color-coded by state |
| **Logs** | Not included | Integrated |
| **Artifacts** | Not shown | Displayed inline |
| **Requirements** | Graphviz | Prefect server running |
| **Use Case** | Documentation, planning | Monitoring, debugging |

## Visualization Patterns

### Linear Flow
```
Task A → Task B → Task C
```
**Use Case:** Sequential processing, ETL pipelines

### Branching Flow
```
       ┌─> Task B ─┐
Task A─┤           ├─> Task D
       └─> Task C ─┘
```
**Use Case:** Conditional logic, different processing paths

### Fan-Out/Fan-In
```
       ┌─> Task B ─┐
Task A─┼─> Task C ─┼─> Task E (aggregate)
       └─> Task D ─┘
```
**Use Case:** Parallel processing, distributed computation

### Multi-Level Dependencies
```
Task A ─┬─> Task B ─┬─> Task D
        └─> Task C ─┘
```
**Use Case:** Complex dependencies, layered processing

## UI Features

### Graph Tab
- **Nodes**: Represent flow runs and task runs
- **Edges**: Show dependencies between tasks
- **Colors**: Indicate task states
  - Gray: Pending
  - Blue: Running
  - Green: Completed
  - Red: Failed
  - Orange: Cancelled

### Interactive Elements
- **Click nodes**: View task details
- **Hover**: See quick info
- **Zoom/Pan**: Navigate large graphs
- **Fullscreen**: Detailed exploration

### Timeline View
- Shows execution duration
- Identifies bottlenecks
- Visualizes parallel execution

## Best Practices for Visualization

### 1. Clear Task Names
```python
@task(name="Extract User Data")  # Clear, descriptive
def extract_users():
    pass
```

### 2. Logical Task Grouping
```python
# Group related tasks
@task
def fetch_data(): pass

@task
def validate_data(): pass

@task
def transform_data(): pass
```

### 3. Avoid Over-Complexity
- Keep flows focused
- Break complex flows into child flows
- Limit to 20-30 tasks per flow for readability

### 4. Use Child Flows
```python
@flow
def process_department(dept_id):
    # Self-contained processing
    pass

@flow
def process_all_departments():
    for dept_id in departments:
        process_department(dept_id)
```

### 5. Add Logging
```python
@task
def process_data(data):
    logger = get_run_logger()
    logger.info(f"Processing {len(data)} records")
    # Visible in UI logs
```

## Limitations of flow.visualize()

⚠️ **Does NOT support:**
- `task.map()` - Cannot visualize dynamic parallel execution
- `task.submit()` - Cannot track async submissions
- Dynamic task creation
- Conditional task creation

✓ **Works with:**
- Direct task calls: `result = my_task()`
- Static dependencies
- Conditional branching (if/else)
- Sequential and parallel patterns

## Accessing the Prefect UI

### Start the Server
```bash
prefect server start
```

### Access UI
```
http://localhost:4200
```

### Navigate to Visualizations
1. **Dashboard** → Overview of recent runs
2. **Flow Runs** → List of all executions
3. **Click run** → Details page
4. **Graph tab** → Workflow visualization

## Troubleshooting

### flow.visualize() Issues

**Error: "Graphviz not found"**
```bash
# Install system library
sudo apt-get install graphviz  # Linux
brew install graphviz          # Mac
```

**Error: "Cannot import graphviz"**
```bash
pip install graphviz
```

### UI Visualization Issues

**Cannot connect to server**
```bash
# Check if server is running
prefect server start

# Check port is accessible
curl http://localhost:4200
```

**Flows not appearing**
```bash
# Run flows after server starts
python your_flow.py

# Check Flow Runs page in UI
```

## Additional Resources

- **Prefect Docs**: https://docs.prefect.io/v3/concepts
- **Graphviz**: https://graphviz.org/
- **UI Guide**: https://docs.prefect.io/v3/manage/interact/ui

## Next Steps

After exploring visualization:
- Use visualizations to optimize workflow design
- Identify bottlenecks from timeline views
- Debug failed runs using graph and logs
- Document workflows with static diagrams
