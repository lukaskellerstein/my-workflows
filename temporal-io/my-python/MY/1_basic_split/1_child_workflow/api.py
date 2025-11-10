"""
FastAPI Workflow Starter - Child Workflow
REST API to start and manage order processing workflows.
"""
import uuid
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from temporalio.client import Client

from workflow_definitions import Order, OrderItem, ProcessOrderWorkflow

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "1-basic-child-workflow-task-queue"

app = FastAPI(
    title="Child Workflow API",
    description="API to start and manage order processing workflows with child workflows",
    version="1.0.0",
)


class OrderItemRequest(BaseModel):
    """Request model for an order item."""

    product: str = Field(..., description="Product name", example="Laptop")
    quantity: int = Field(..., description="Quantity", example=1, gt=0)
    price: float = Field(..., description="Unit price", example=999.99, gt=0)


class OrderRequest(BaseModel):
    """Request model for starting an order workflow."""

    order_id: str = Field(..., description="Order ID", example="ORD-12345")
    customer: str = Field(..., description="Customer name", example="John Doe")
    items: List[OrderItemRequest] = Field(..., description="List of order items", min_length=1)
    workflow_id: Optional[str] = Field(
        None, description="Optional workflow ID (auto-generated if not provided)"
    )


class WorkflowResponse(BaseModel):
    """Response model for workflow execution."""

    workflow_id: str = Field(..., description="The workflow instance ID")
    order_id: str = Field(..., description="The order ID")
    result: str = Field(..., description="The workflow execution result")
    status: str = Field(..., description="Execution status")


class WorkflowInfo(BaseModel):
    """Information about the workflow."""

    description: str
    workflow_types: List[str]
    process_flow: List[str]


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Child Workflow API",
        "version": "1.0.0",
        "description": "Order processing with parent and child workflows",
        "endpoints": {
            "start_order": "/order/start",
            "workflow_info": "/workflow/info",
            "health": "/health",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        client = await Client.connect(TEMPORAL_HOST)
        return {"status": "healthy", "temporal_connected": True}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Temporal connection failed: {str(e)}")


@app.get("/workflow/info", response_model=WorkflowInfo)
async def workflow_info():
    """Get information about the workflow structure."""
    return WorkflowInfo(
        description="Order processing using parent-child workflow pattern",
        workflow_types=[
            "ProcessOrderWorkflow (Parent) - Orchestrates the entire order",
            "ProcessOrderItemWorkflow (Child) - Processes individual items",
        ],
        process_flow=[
            "1. Parent workflow receives order",
            "2. For each item, spawn a child workflow",
            "3. Child workflows validate inventory and calculate subtotals",
            "4. Parent aggregates subtotals",
            "5. Parent processes payment",
            "6. Parent ships order",
        ],
    )


@app.post("/order/start", response_model=WorkflowResponse)
async def start_order(request: OrderRequest):
    """
    Start a new order processing workflow.

    The parent workflow delegates item processing to child workflows,
    demonstrating modular and reusable workflow components.

    Args:
        request: Order request with items and customer details

    Returns:
        Workflow execution result
    """
    try:
        # Connect to Temporal server
        client = await Client.connect(TEMPORAL_HOST)

        # Generate workflow ID if not provided
        workflow_id = request.workflow_id or f"child-workflow-order-{uuid.uuid4()}"

        # Convert request items to OrderItem objects
        items = [
            OrderItem(product=item.product, quantity=item.quantity, price=item.price)
            for item in request.items
        ]

        # Create order
        order = Order(order_id=request.order_id, customer=request.customer, items=items)

        # Start and wait for workflow completion
        result = await client.execute_workflow(
            ProcessOrderWorkflow.run,
            order,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )

        return WorkflowResponse(
            workflow_id=workflow_id,
            order_id=request.order_id,
            result=result,
            status="completed",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
