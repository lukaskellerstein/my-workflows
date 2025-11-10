"""
FastAPI Workflow Starter - Human in the Loop
REST API to start expense approval workflows and send signals.
"""
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from temporalio.client import Client

from workflow_definitions import ApprovalDecision, ExpenseApprovalWorkflow, ExpenseRequest

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "1-basic-human-in-loop-task-queue"

app = FastAPI(
    title="Human in the Loop API",
    description="API for expense approval workflows with human decision-making",
    version="1.0.0",
)


class ExpenseRequestModel(BaseModel):
    """Request model for starting an expense approval workflow."""

    employee: str = Field(..., description="Employee name", example="John Doe")
    amount: float = Field(..., description="Expense amount", example=2500.00, gt=0)
    category: str = Field(..., description="Expense category", example="Travel")
    description: str = Field(
        ..., description="Expense description", example="Conference attendance"
    )
    workflow_id: Optional[str] = Field(
        None, description="Optional workflow ID (auto-generated if not provided)"
    )


class ApprovalDecisionModel(BaseModel):
    """Model for approval/rejection decision."""

    approver: str = Field(..., description="Name of the approver", example="Manager Sarah")
    comments: str = Field(..., description="Decision comments", example="Approved for Q1 budget")


class WorkflowResponse(BaseModel):
    """Response model for workflow operations."""

    workflow_id: str = Field(..., description="The workflow instance ID")
    message: str = Field(..., description="Response message")
    status: str = Field(..., description="Current status")


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status query."""

    workflow_id: str
    status: str
    message: str


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Human in the Loop API",
        "version": "1.0.0",
        "description": "Expense approval workflows with human decision-making via signals",
        "endpoints": {
            "start_expense": "/expense/start",
            "approve": "/expense/{workflow_id}/approve",
            "reject": "/expense/{workflow_id}/reject",
            "status": "/expense/{workflow_id}/status",
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


@app.post("/expense/start", response_model=WorkflowResponse)
async def start_expense(request: ExpenseRequestModel):
    """
    Start a new expense approval workflow.

    Small amounts (≤$100) are auto-approved.
    Larger amounts require manual approval via signals.

    Args:
        request: Expense request details

    Returns:
        Workflow ID and status
    """
    try:
        # Connect to Temporal server
        client = await Client.connect(TEMPORAL_HOST)

        # Generate workflow ID if not provided
        workflow_id = request.workflow_id or f"expense-approval-{uuid.uuid4()}"

        # Create expense request
        expense = ExpenseRequest(
            employee=request.employee,
            amount=request.amount,
            category=request.category,
            description=request.description,
        )

        # Start workflow (don't wait for completion)
        await client.start_workflow(
            ExpenseApprovalWorkflow.run,
            expense,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )

        # Determine message based on amount
        if request.amount <= 100:
            message = "Expense submitted for auto-approval"
            status = "auto_approving"
        else:
            message = "Expense submitted. Waiting for manager approval."
            status = "pending_approval"

        return WorkflowResponse(workflow_id=workflow_id, message=message, status=status)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


@app.post("/expense/{workflow_id}/approve", response_model=WorkflowResponse)
async def approve_expense(workflow_id: str, decision: ApprovalDecisionModel):
    """
    Approve an expense by sending an approval signal.

    Args:
        workflow_id: The workflow ID to approve
        decision: Approval decision with approver name and comments

    Returns:
        Confirmation of signal sent
    """
    try:
        client = await Client.connect(TEMPORAL_HOST)

        # Get workflow handle
        handle = client.get_workflow_handle(workflow_id)

        # Create approval decision
        approval = ApprovalDecision(
            approved=True, approver=decision.approver, comments=decision.comments
        )

        # Send approval signal
        await handle.signal(ExpenseApprovalWorkflow.approve, approval)

        return WorkflowResponse(
            workflow_id=workflow_id,
            message=f"Approval signal sent by {decision.approver}",
            status="approved",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send approval: {str(e)}")


@app.post("/expense/{workflow_id}/reject", response_model=WorkflowResponse)
async def reject_expense(workflow_id: str, decision: ApprovalDecisionModel):
    """
    Reject an expense by sending a rejection signal.

    Args:
        workflow_id: The workflow ID to reject
        decision: Rejection decision with approver name and comments

    Returns:
        Confirmation of signal sent
    """
    try:
        client = await Client.connect(TEMPORAL_HOST)

        # Get workflow handle
        handle = client.get_workflow_handle(workflow_id)

        # Create rejection decision
        rejection = ApprovalDecision(
            approved=False, approver=decision.approver, comments=decision.comments
        )

        # Send rejection signal
        await handle.signal(ExpenseApprovalWorkflow.reject, rejection)

        return WorkflowResponse(
            workflow_id=workflow_id,
            message=f"Rejection signal sent by {decision.approver}",
            status="rejected",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send rejection: {str(e)}")


@app.get("/expense/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_expense_status(workflow_id: str):
    """
    Query the current status of an expense approval workflow.

    Args:
        workflow_id: The workflow ID to query

    Returns:
        Current workflow status
    """
    try:
        client = await Client.connect(TEMPORAL_HOST)

        # Get workflow handle
        handle = client.get_workflow_handle(workflow_id)

        # Query status
        status = await handle.query(ExpenseApprovalWorkflow.get_status)

        status_messages = {
            "pending": "Waiting for approval decision",
            "approved": "Expense has been approved",
            "rejected": "Expense has been rejected",
            "timeout": "Approval timeout - automatically rejected",
        }

        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            status=status,
            message=status_messages.get(status, "Unknown status"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query status: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
