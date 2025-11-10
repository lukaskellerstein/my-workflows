"""REST API for HR approval workflow with Updates."""

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from temporalio.client import Client

from models import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalState,
    Priority,
    RequestType,
)
from workflows import HRApprovalWorkflow

app = FastAPI(title="HR Approval API - Temporal Updates Demo")

# Global client (initialized on startup)
temporal_client: Optional[Client] = None


class CreateRequestModel(BaseModel):
    """Request to create a new approval request."""
    employee_id: str
    employee_name: str
    request_type: RequestType
    title: str
    description: str
    priority: Priority = Priority.MEDIUM
    amount: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class SubmitApprovalModel(BaseModel):
    """Request to submit an approval decision."""
    approver_id: str
    approver_name: str
    approved: bool
    comments: str


class AddCommentsModel(BaseModel):
    """Request to add comments."""
    commenter_name: str
    comments: str


class CancelRequestModel(BaseModel):
    """Request to cancel."""
    reason: str


@app.on_event("startup")
async def startup():
    """Initialize Temporal client on startup."""
    global temporal_client
    temporal_client = await Client.connect("localhost:7233")
    print("✅ Connected to Temporal server")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    if temporal_client:
        await temporal_client.close()


@app.post("/requests", status_code=201)
async def create_request(request: CreateRequestModel):
    """
    Create a new approval request and start the workflow.

    This initiates the HR approval workflow in Temporal.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    # Generate request ID
    request_id = f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Parse dates if provided
    start_date = datetime.fromisoformat(request.start_date) if request.start_date else None
    end_date = datetime.fromisoformat(request.end_date) if request.end_date else None

    # Create approval request
    approval_request = ApprovalRequest(
        request_id=request_id,
        employee_id=request.employee_id,
        employee_name=request.employee_name,
        request_type=request.request_type,
        title=request.title,
        description=request.description,
        priority=request.priority,
        amount=request.amount,
        start_date=start_date,
        end_date=end_date,
    )

    # Start workflow
    handle = await temporal_client.start_workflow(
        HRApprovalWorkflow.run,
        approval_request,
        id=f"approval-{request_id}",
        task_queue="hr-approval-queue",
    )

    return {
        "request_id": request_id,
        "workflow_id": handle.id,
        "status": "pending",
        "message": "Approval request created. Awaiting manager approval."
    }


@app.post("/requests/{request_id}/manager-approval")
async def submit_manager_approval(request_id: str, approval: SubmitApprovalModel):
    """
    Submit manager approval decision (UPDATE).

    This demonstrates the UPDATE pattern:
    - Sends approval decision to workflow
    - Workflow validates the decision
    - Returns updated state immediately
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"approval-{request_id}"

    try:
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Create decision
        decision = ApprovalDecision(
            approver_id=approval.approver_id,
            approver_name=approval.approver_name,
            approved=approval.approved,
            comments=approval.comments,
            timestamp=datetime.now()
        )

        # Execute UPDATE - sends data in AND gets data back
        updated_state: ApprovalState = await handle.execute_update(
            HRApprovalWorkflow.submit_manager_approval,
            decision
        )

        return {
            "request_id": request_id,
            "message": f"Manager {'approved' if approval.approved else 'rejected'} the request",
            "updated_state": {
                "status": updated_state.status.value,
                "updated_at": updated_state.updated_at.isoformat(),
                "manager_decision": {
                    "approver": updated_state.manager_decision.approver_name,
                    "approved": updated_state.manager_decision.approved,
                    "comments": updated_state.manager_decision.comments,
                } if updated_state.manager_decision else None
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to submit manager approval: {str(e)}"
        )


@app.post("/requests/{request_id}/hr-approval")
async def submit_hr_approval(request_id: str, approval: SubmitApprovalModel):
    """
    Submit HR approval decision (UPDATE).

    This is the final approval step. Returns complete updated state.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"approval-{request_id}"

    try:
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Create decision
        decision = ApprovalDecision(
            approver_id=approval.approver_id,
            approver_name=approval.approver_name,
            approved=approval.approved,
            comments=approval.comments,
            timestamp=datetime.now()
        )

        # Execute UPDATE
        updated_state: ApprovalState = await handle.execute_update(
            HRApprovalWorkflow.submit_hr_approval,
            decision
        )

        return {
            "request_id": request_id,
            "message": f"HR {'approved' if approval.approved else 'rejected'} the request",
            "final_status": updated_state.status.value,
            "updated_state": {
                "status": updated_state.status.value,
                "updated_at": updated_state.updated_at.isoformat(),
                "completed_at": updated_state.completed_at.isoformat() if updated_state.completed_at else None,
                "hr_decision": {
                    "approver": updated_state.hr_decision.approver_name,
                    "approved": updated_state.hr_decision.approved,
                    "comments": updated_state.hr_decision.comments,
                } if updated_state.hr_decision else None
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to submit HR approval: {str(e)}"
        )


@app.post("/requests/{request_id}/comments")
async def add_comments(request_id: str, comment: AddCommentsModel):
    """
    Add comments to the request (UPDATE).

    Demonstrates lightweight updates that don't affect approval logic.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"approval-{request_id}"

    try:
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Execute UPDATE
        result = await handle.execute_update(
            HRApprovalWorkflow.add_comments,
            comment.commenter_name,
            comment.comments
        )

        return {
            "request_id": request_id,
            "message": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to add comments: {str(e)}"
        )


@app.delete("/requests/{request_id}")
async def cancel_request(request_id: str, cancel: CancelRequestModel):
    """
    Cancel the approval request (SIGNAL).

    Demonstrates Signal for one-way cancellation.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"approval-{request_id}"

    try:
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Send cancellation signal
        await handle.signal(HRApprovalWorkflow.cancel_request, cancel.reason)

        return {
            "request_id": request_id,
            "message": "Cancellation initiated",
            "reason": cancel.reason
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Request not found: {str(e)}")


@app.get("/requests/{request_id}/status")
async def get_status(request_id: str):
    """
    Query the current request status (QUERY).

    Read-only operation.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"approval-{request_id}"

    try:
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Query status
        status = await handle.query(HRApprovalWorkflow.get_status)

        return {
            "request_id": request_id,
            "status": status
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Request not found: {str(e)}")


@app.get("/requests/{request_id}")
async def get_request_details(request_id: str):
    """
    Query complete request details (QUERY).

    Read-only operation retrieving full state.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"approval-{request_id}"

    try:
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Query full state
        state: ApprovalState = await handle.query(HRApprovalWorkflow.get_full_state)

        return {
            "request_id": state.request_id,
            "employee_id": state.employee_id,
            "employee_name": state.employee_name,
            "request_type": state.request_type.value,
            "title": state.title,
            "description": state.description,
            "priority": state.priority.value,
            "status": state.status.value,
            "manager_decision": {
                "approver_id": state.manager_decision.approver_id,
                "approver_name": state.manager_decision.approver_name,
                "approved": state.manager_decision.approved,
                "comments": state.manager_decision.comments,
                "timestamp": state.manager_decision.timestamp.isoformat()
            } if state.manager_decision else None,
            "hr_decision": {
                "approver_id": state.hr_decision.approver_id,
                "approver_name": state.hr_decision.approver_name,
                "approved": state.hr_decision.approved,
                "comments": state.hr_decision.comments,
                "timestamp": state.hr_decision.timestamp.isoformat()
            } if state.hr_decision else None,
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
            "completed_at": state.completed_at.isoformat() if state.completed_at else None,
            "cancellation_reason": state.cancellation_reason
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Request not found: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "temporal_connected": temporal_client is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
