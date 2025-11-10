"""
FastAPI Workflow Starter
REST API to start and query workflow instances.
"""
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from temporalio.client import Client

from workflow_definitions import SingleNodeWorkflow

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "0-simple-single-node-task-queue"

app = FastAPI(
    title="Single Node Workflow API",
    description="API to start and manage simple Temporal workflows",
    version="1.0.0",
)


class WorkflowRequest(BaseModel):
    """Request model for starting a workflow."""

    input_value: int = Field(..., description="The input value to process")
    workflow_id: Optional[str] = Field(
        None, description="Optional workflow ID (auto-generated if not provided)"
    )


class WorkflowResponse(BaseModel):
    """Response model for workflow execution."""

    workflow_id: str = Field(..., description="The workflow instance ID")
    result: int = Field(..., description="The workflow execution result")
    status: str = Field(..., description="Execution status")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Single Node Workflow API",
        "version": "1.0.0",
        "endpoints": {
            "start_workflow": "/workflow/start",
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


@app.post("/workflow/start", response_model=WorkflowResponse)
async def start_workflow(request: WorkflowRequest):
    """
    Start a new workflow instance.

    Args:
        request: Workflow request with input value and optional workflow ID

    Returns:
        Workflow execution result
    """
    try:
        # Connect to Temporal server
        client = await Client.connect(TEMPORAL_HOST)

        # Generate workflow ID if not provided
        workflow_id = request.workflow_id or f"single-node-workflow-{uuid.uuid4()}"

        # Start and wait for workflow completion
        result = await client.execute_workflow(
            SingleNodeWorkflow.run,
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

    uvicorn.run(app, host="0.0.0.0", port=8000)
