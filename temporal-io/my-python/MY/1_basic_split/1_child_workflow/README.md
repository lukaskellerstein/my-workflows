# Child Workflow Example

Demonstrates how to use child workflows for modular, reusable workflow components. Parent workflows delegate subtasks to child workflows, enabling better code organization and parallel processing.

## Architecture

This example separates concerns into distinct components:

- **`workflow_definitions.py`** - Parent and child workflow definitions, activities, and data models
- **`worker.py`** - Worker script that processes both parent and child workflows
- **`start_workflow.py`** - Python script to start order processing workflows
- **`api.py`** - FastAPI REST API to start workflows via HTTP

## Workflow Structure

### Parent Workflow: ProcessOrderWorkflow

Orchestrates the entire order processing by:
1. Spawning child workflows for each order item
2. Aggregating results from child workflows
3. Processing payment
4. Shipping the order

### Child Workflow: ProcessOrderItemWorkflow

Processes individual order items by:
1. Validating inventory availability
2. Calculating item subtotal

## Workflow Flow

```
Parent Workflow (ProcessOrderWorkflow)
├── Child Workflow: Item 1 (ProcessOrderItemWorkflow)
│   ├── Activity: validate_inventory
│   └── Activity: calculate_subtotal
├── Child Workflow: Item 2 (ProcessOrderItemWorkflow)
│   ├── Activity: validate_inventory
│   └── Activity: calculate_subtotal
├── Child Workflow: Item 3 (ProcessOrderItemWorkflow)
│   ├── Activity: validate_inventory
│   └── Activity: calculate_subtotal
├── Activity: process_payment (total from all items)
└── Activity: ship_order
```

## Prerequisites

1. Temporal server running locally on `localhost:7233`
2. Python dependencies installed via `uv sync`

## Usage

### 1. Start the Worker

The worker must be running to process both parent and child workflows:

```bash
cd MY/1_basic_split/1_child_workflow
uv run python worker.py
```

Output:
```
Connected to Temporal at localhost:7233
Worker started on task queue: 1-basic-child-workflow-task-queue
Max concurrent activities: 10
Registered workflows:
  - ProcessOrderWorkflow (parent)
  - ProcessOrderItemWorkflow (child)
Registered activities:
  - validate_inventory, calculate_subtotal, process_payment, ship_order
Press Ctrl+C to stop the worker
```

### 2. Start Workflows

#### Option A: Python Script

Simple script to start order workflows:

```bash
uv run python start_workflow.py
```

**Programmatic usage:**

```python
import asyncio
from start_workflow import start_workflow
from workflow_definitions import Order, OrderItem

# Create order
order = Order(
    order_id="ORD-12345",
    customer="John Doe",
    items=[
        OrderItem(product="Laptop", quantity=1, price=999.99),
        OrderItem(product="Mouse", quantity=2, price=29.99),
    ]
)

# Start workflow
result = asyncio.run(start_workflow(order))
```

#### Option B: FastAPI REST API

Start the API server:

```bash
uv run python api.py
```

The API will be available at `http://localhost:8002`

**Endpoints:**

1. **Get Workflow Info**
   ```bash
   curl http://localhost:8002/workflow/info
   ```

2. **Health Check**
   ```bash
   curl http://localhost:8002/health
   ```

3. **Start Order Processing**
   ```bash
   curl -X POST http://localhost:8002/order/start \
     -H "Content-Type: application/json" \
     -d '{
       "order_id": "ORD-12345",
       "customer": "John Doe",
       "items": [
         {"product": "Laptop", "quantity": 1, "price": 999.99},
         {"product": "Mouse", "quantity": 2, "price": 29.99},
         {"product": "Keyboard", "quantity": 1, "price": 79.99}
       ]
     }'
   ```

   With custom workflow ID:
   ```bash
   curl -X POST http://localhost:8002/order/start \
     -H "Content-Type: application/json" \
     -d '{
       "order_id": "ORD-67890",
       "customer": "Jane Smith",
       "workflow_id": "my-order-workflow",
       "items": [
         {"product": "Monitor", "quantity": 2, "price": 299.99}
       ]
     }'
   ```

4. **API Documentation**

   Interactive API docs available at:
   - Swagger UI: `http://localhost:8002/docs`
   - ReDoc: `http://localhost:8002/redoc`

## Configuration

All scripts use the following configuration:

- **Temporal Host**: `localhost:7233`
- **Task Queue**: `1-basic-child-workflow-task-queue`
- **Max Concurrent Activities**: 10
- **API Port**: 8002

To modify these, edit the constants at the top of each file.

## Example Execution

### Sample Order

```python
Order(
    order_id="ORD-12345",
    customer="John Doe",
    items=[
        OrderItem(product="Laptop", quantity=1, price=999.99),
        OrderItem(product="Mouse", quantity=2, price=29.99),
        OrderItem(product="Keyboard", quantity=1, price=79.99),
    ]
)
```

### Execution Flow

1. **Parent workflow starts** for order ORD-12345
2. **Three child workflows spawn** in parallel:
   - Child 1: Process Laptop → Subtotal: $999.99
   - Child 2: Process Mouse → Subtotal: $59.98
   - Child 3: Process Keyboard → Subtotal: $79.99
3. **Parent aggregates** subtotals: $1,139.96
4. **Payment processed**: $1,139.96
5. **Order shipped** to John Doe

### Result

```
Order ORD-12345 completed:
  - Payment successful: $1139.96
  - Order ORD-12345 shipped to John Doe
  - Items processed: 3
```

## Benefits of Child Workflows

1. **Modularity**: Item processing logic is encapsulated in child workflows
2. **Reusability**: Child workflows can be reused by different parent workflows
3. **Parallel Execution**: Multiple child workflows can run concurrently
4. **Independent Lifecycle**: Each child has its own workflow ID and history
5. **Fault Isolation**: Child workflow failures don't automatically fail the parent
6. **Scalability**: Each child workflow can be retried independently

## File Structure

```
1_child_workflow/
├── workflow_definitions.py   # Parent and child workflows, activities
├── worker.py                  # Worker script
├── start_workflow.py          # Python workflow starter
├── api.py                     # FastAPI workflow starter
└── README.md                  # This file
```

## Key Differences from Previous Examples

1. **Parent-Child Pattern**: Workflows can spawn other workflows
2. **Parallel Child Execution**: Multiple child workflows run concurrently
3. **Hierarchical Structure**: Clear parent-child relationship
4. **Modular Design**: Reusable child workflow components
5. **Complex Data Models**: Uses dataclasses for structured data

## Development Notes

- The worker must be running before starting workflows
- Worker must register both parent and child workflows
- Each child workflow gets a unique ID: `{order_id}-item-{product}`
- Child workflows run on the same task queue as parent
- All components use async/await for non-blocking operations
- Temporal UI shows parent-child relationship in workflow history
