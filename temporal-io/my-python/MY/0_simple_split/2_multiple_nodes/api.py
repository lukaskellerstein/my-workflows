"""
FastAPI Workflow Starter - Multiple Nodes
REST API to start and query multiple-nodes workflow instances.
"""
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from temporalio.client import Client

from workflow_definitions import MultipleNodesWorkflow

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "0-simple-multiple-nodes-task-queue"

app = FastAPI(
    title="Multiple Nodes Workflow API",
    description="API to start and manage multi-step Temporal workflows with sequential activities",
    version="1.0.0",
)


class WorkflowRequest(BaseModel):
    """Request model for starting a workflow."""

    input_value: int = Field(
        ...,
        description="The input value to process (must be positive to pass validation)",
        example=15,
    )
    workflow_id: Optional[str] = Field(
        None, description="Optional workflow ID (auto-generated if not provided)"
    )


class WorkflowResponse(BaseModel):
    """Response model for workflow execution."""

    workflow_id: str = Field(..., description="The workflow instance ID")
    result: str = Field(..., description="The workflow execution result message")
    status: str = Field(..., description="Execution status")


class WorkflowSteps(BaseModel):
    """Information about workflow steps."""

    steps: list[str] = Field(..., description="List of workflow steps")
    description: str = Field(..., description="Workflow description")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Multiple Nodes Workflow API",
        "version": "1.0.0",
        "description": "Multi-step workflow with validation, transformation, and saving",
        "endpoints": {
            "start_workflow": "/workflow/start",
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


@app.get("/workflow/info", response_model=WorkflowSteps)
async def workflow_info():
    """Get information about the workflow steps."""
    return WorkflowSteps(
        description="Sequential multi-step workflow processing",
        steps=[
            "1. Validate Input - Check if input value is positive",
            "2. Transform Data - Apply transformation (value * 3 + 10)",
            "3. Save Result - Save the transformed value",
        ],
    )


@app.post("/workflow/start", response_model=WorkflowResponse)
async def start_workflow(request: WorkflowRequest):
    """
    Start a new multiple-nodes workflow instance.

    The workflow executes three sequential activities:
    1. Validate the input (must be positive)
    2. Transform the data
    3. Save the result

    Args:
        request: Workflow request with input value and optional workflow ID

    Returns:
        Workflow execution result
    """
    try:
        # Connect to Temporal server
        client = await Client.connect(TEMPORAL_HOST)

        # Generate workflow ID if not provided
        workflow_id = request.workflow_id or f"multiple-nodes-workflow-{uuid.uuid4()}"

        # Start and wait for workflow completion
        result = await client.execute_workflow(
            MultipleNodesWorkflow.run,
            request.input_value,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )

        return WorkflowResponse(
            workflow_id=workflow_id,
            result=result,
            status="completed",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
