"""
Workflow Starter Script - Human in the Loop
Simple Python script to start expense approval workflows and send signals.
"""
import asyncio
import uuid

from temporalio.client import Client

from workflow_definitions import ApprovalDecision, ExpenseApprovalWorkflow, ExpenseRequest

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "1-basic-human-in-loop-task-queue"


async def start_and_wait_workflow(request: ExpenseRequest, workflow_id: str = None) -> str:
    """
    Start an expense approval workflow and wait for completion (auto-approval only).

    Args:
        request: The expense request
        workflow_id: Optional workflow ID (auto-generated if not provided)

    Returns:
        The workflow result
    """
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)

    # Generate workflow ID if not provided
    if workflow_id is None:
        workflow_id = f"expense-approval-{uuid.uuid4()}"

    print(f"Starting workflow with ID: {workflow_id}")
    print(f"Employee: {request.employee}")
    print(f"Amount: ${request.amount}")
    print(f"Category: {request.category}")

    # Start and wait for workflow completion
    result = await client.execute_workflow(
        ExpenseApprovalWorkflow.run,
        request,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    print(f"\n{result}")
    return result


async def start_workflow_with_manual_approval(
    request: ExpenseRequest, workflow_id: str = None
) -> str:
    """
    Start an expense approval workflow that requires manual approval.

    Args:
        request: The expense request
        workflow_id: Optional workflow ID (auto-generated if not provided)

    Returns:
        The workflow ID for later signaling
    """
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)

    # Generate workflow ID if not provided
    if workflow_id is None:
        workflow_id = f"expense-approval-{uuid.uuid4()}"

    print(f"Starting workflow with ID: {workflow_id}")
    print(f"Employee: {request.employee}")
    print(f"Amount: ${request.amount}")
    print(f"Category: {request.category}")

    # Start workflow (don't wait)
    handle = await client.start_workflow(
        ExpenseApprovalWorkflow.run,
        request,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    print(f"\nWorkflow started. Waiting for approval...")
    print(f"Workflow ID: {workflow_id}")
    print("\nTo approve: Use send_approval_signal.py")
    print("To reject: Use send_rejection_signal.py")
    print("To check status: Use query_workflow.py")

    return workflow_id


async def send_approval(workflow_id: str, approver: str, comments: str):
    """
    Send approval signal to a running workflow.

    Args:
        workflow_id: The workflow ID to signal
        approver: Name of the approver
        comments: Approval comments
    """
    client = await Client.connect(TEMPORAL_HOST)

    # Get workflow handle
    handle = client.get_workflow_handle(workflow_id)

    # Send approval signal
    decision = ApprovalDecision(approved=True, approver=approver, comments=comments)

    await handle.signal(ExpenseApprovalWorkflow.approve, decision)

    print(f"Approval signal sent to workflow {workflow_id}")
    print(f"Approver: {approver}")
    print(f"Comments: {comments}")

    # Wait for workflow completion
    result = await handle.result()
    print(f"\nWorkflow completed:\n{result}")


async def send_rejection(workflow_id: str, approver: str, comments: str):
    """
    Send rejection signal to a running workflow.

    Args:
        workflow_id: The workflow ID to signal
        approver: Name of the approver
        comments: Rejection comments
    """
    client = await Client.connect(TEMPORAL_HOST)

    # Get workflow handle
    handle = client.get_workflow_handle(workflow_id)

    # Send rejection signal
    decision = ApprovalDecision(approved=False, approver=approver, comments=comments)

    await handle.signal(ExpenseApprovalWorkflow.reject, decision)

    print(f"Rejection signal sent to workflow {workflow_id}")
    print(f"Approver: {approver}")
    print(f"Comments: {comments}")

    # Wait for workflow completion
    result = await handle.result()
    print(f"\nWorkflow completed:\n{result}")


async def query_workflow_status(workflow_id: str):
    """
    Query the status of a running workflow.

    Args:
        workflow_id: The workflow ID to query
    """
    client = await Client.connect(TEMPORAL_HOST)

    # Get workflow handle
    handle = client.get_workflow_handle(workflow_id)

    # Query status
    status = await handle.query(ExpenseApprovalWorkflow.get_status)

    print(f"Workflow ID: {workflow_id}")
    print(f"Current status: {status}")


async def main():
    """Main entry point with examples."""
    print("=== Example 1: Auto-Approval (Small Amount) ===\n")

    # Small expense - auto-approved
    request1 = ExpenseRequest(
        employee="John Doe",
        amount=75.50,
        category="Office Supplies",
        description="Pens and notebooks",
    )

    await start_and_wait_workflow(request1)

    print("\n" + "=" * 50)
    print("=== Example 2: Manual Approval Required ===\n")

    # Large expense - requires approval
    request2 = ExpenseRequest(
        employee="Jane Smith",
        amount=2500.00,
        category="Travel",
        description="Conference attendance and hotel",
    )

    workflow_id = await start_workflow_with_manual_approval(request2)

    # Wait a bit, then check status
    await asyncio.sleep(2)
    await query_workflow_status(workflow_id)

    # Simulate approval
    print("\n[Simulating manager approval...]")
    await asyncio.sleep(2)

    await send_approval(
        workflow_id=workflow_id,
        approver="Manager Sarah Johnson",
        comments="Conference attendance is valuable for professional development",
    )


if __name__ == "__main__":
    asyncio.run(main())
