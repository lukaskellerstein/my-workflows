"""
Example: Human in the Loop
This demonstrates workflows that require human approval or decision-making.
The workflow pauses and waits for human input via signals before continuing.
"""
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


@dataclass
class ExpenseRequest:
    employee: str
    amount: float
    category: str
    description: str


@dataclass
class ApprovalDecision:
    approved: bool
    approver: str
    comments: str


@dataclass
class EmployeeNotification:
    request: ExpenseRequest
    status: str  # Store as string instead of enum


# Activities


@activity.defn
def validate_expense(request: ExpenseRequest) -> bool:
    activity.logger.info(f"Validating expense request from {request.employee}")
    # Validate expense rules
    if request.amount <= 0:
        return False
    if request.amount > 100000:  # Max limit
        return False
    return True


@activity.defn
def notify_approver(request: ExpenseRequest) -> str:
    activity.logger.info(
        f"Notifying approver about ${request.amount} expense from {request.employee}"
    )
    # In real scenario: send email, Slack message, etc.
    return f"Notification sent to approver for {request.employee}'s expense"


@activity.defn
def process_approved_expense(request: ExpenseRequest) -> str:
    activity.logger.info(f"Processing approved expense of ${request.amount}")
    # In real scenario: update accounting system, trigger payment
    return f"Expense of ${request.amount} processed for {request.employee}"


@activity.defn
def notify_employee(notification: EmployeeNotification) -> str:
    activity.logger.info(
        f"Notifying {notification.request.employee} about {notification.status} expense"
    )
    # In real scenario: send email to employee
    return f"Employee {notification.request.employee} notified: {notification.status}"


# Workflow with human approval


@workflow.defn
class ExpenseApprovalWorkflow:
    def __init__(self) -> None:
        self._approval_status = ApprovalStatus.PENDING
        self._approval_decision: ApprovalDecision | None = None

    @workflow.run
    async def run(self, request: ExpenseRequest) -> str:
        workflow.logger.info(
            f"Expense approval workflow started for {request.employee}: ${request.amount}"
        )

        # Step 1: Validate expense
        is_valid = await workflow.execute_activity(
            validate_expense,
            request,
            start_to_close_timeout=timedelta(seconds=10),
        )

        if not is_valid:
            workflow.logger.warning("Expense validation failed")
            return "Expense request rejected: Invalid request"

        # Step 2: Check if auto-approval is possible (e.g., small amounts)
        if request.amount <= 100:
            workflow.logger.info("Auto-approved: Amount below threshold")
            self._approval_status = ApprovalStatus.APPROVED
            self._approval_decision = ApprovalDecision(
                approved=True,
                approver="Auto-Approval System",
                comments="Amount below $100 threshold",
            )
        else:
            # Step 3: Notify approver - Human intervention required
            await workflow.execute_activity(
                notify_approver,
                request,
                start_to_close_timeout=timedelta(seconds=10),
            )

            workflow.logger.info("Waiting for human approval...")

            # Wait for approval signal (with timeout)
            try:
                await workflow.wait_condition(
                    lambda: self._approval_status != ApprovalStatus.PENDING,
                    timeout=timedelta(hours=24),  # 24-hour approval window
                )
            except asyncio.TimeoutError:
                workflow.logger.warning("Approval timeout - auto-rejecting")
                self._approval_status = ApprovalStatus.TIMEOUT
                self._approval_decision = ApprovalDecision(
                    approved=False,
                    approver="System",
                    comments="No response within 24 hours",
                )

        # Step 4: Process based on approval decision
        if self._approval_status == ApprovalStatus.APPROVED:
            # Process the expense
            process_result = await workflow.execute_activity(
                process_approved_expense,
                request,
                start_to_close_timeout=timedelta(seconds=10),
            )

            # Notify employee
            await workflow.execute_activity(
                notify_employee,
                EmployeeNotification(request=request, status=ApprovalStatus.APPROVED.value),
                start_to_close_timeout=timedelta(seconds=10),
            )

            return (
                f"Expense APPROVED by {self._approval_decision.approver}\n"
                f"Comments: {self._approval_decision.comments}\n"
                f"{process_result}"
            )
        else:
            # Notify employee of rejection
            await workflow.execute_activity(
                notify_employee,
                EmployeeNotification(request=request, status=self._approval_status.value),
                start_to_close_timeout=timedelta(seconds=10),
            )

            reason = (
                self._approval_decision.comments
                if self._approval_decision
                else "Unknown reason"
            )
            return f"Expense REJECTED: {reason}"

    @workflow.signal
    async def approve(self, decision: ApprovalDecision) -> None:
        """Signal sent by approver to approve the expense"""
        workflow.logger.info(f"Approval received from {decision.approver}")
        self._approval_status = ApprovalStatus.APPROVED
        self._approval_decision = decision

    @workflow.signal
    async def reject(self, decision: ApprovalDecision) -> None:
        """Signal sent by approver to reject the expense"""
        workflow.logger.info(f"Rejection received from {decision.approver}")
        self._approval_status = ApprovalStatus.REJECTED
        self._approval_decision = decision

    @workflow.query
    def get_status(self) -> str:
        """Query to check current approval status"""
        return self._approval_status.value

    @workflow.query
    def get_request_details(self) -> ExpenseRequest:
        """Query to get the expense request details"""
        # Note: This would be stored as instance variable in real implementation
        return None


async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue="1-basic-human-in-loop-task-queue",
        workflows=[ExpenseApprovalWorkflow],
        activities=[
            validate_expense,
            notify_approver,
            process_approved_expense,
            notify_employee,
        ],
        activity_executor=ThreadPoolExecutor(5),
    ):
        print("=== Example 1: Auto-Approval (Small Amount) ===\n")

        # Small expense - auto-approved
        request1 = ExpenseRequest(
            employee="John Doe",
            amount=75.50,
            category="Office Supplies",
            description="Pens and notebooks",
        )

        result1 = await client.execute_workflow(
            ExpenseApprovalWorkflow.run,
            request1,
            id=f"1-basic-human-in-loop-auto-approval-{uuid.uuid4()}",
            task_queue="1-basic-human-in-loop-task-queue",
        )
        print(f"Result: {result1}\n")

        print("\n=== Example 2: Manual Approval Required ===\n")

        # Large expense - requires approval
        request2 = ExpenseRequest(
            employee="Jane Smith",
            amount=2500.00,
            category="Travel",
            description="Conference attendance and hotel",
        )

        # Start workflow (don't wait)
        handle = await client.start_workflow(
            ExpenseApprovalWorkflow.run,
            request2,
            id=f"1-basic-human-in-loop-manual-approval-{uuid.uuid4()}",
            task_queue="1-basic-human-in-loop-task-queue",
        )

        print(f"Expense request submitted for ${request2.amount}")
        print("Waiting for approval...\n")

        # Check status
        await asyncio.sleep(1)
        status = await handle.query(ExpenseApprovalWorkflow.get_status)
        print(f"Current status: {status}")

        # Simulate human approver making a decision
        print("\n[Simulating manager approval after review...]")
        await asyncio.sleep(2)

        # Manager approves
        await handle.signal(
            ExpenseApprovalWorkflow.approve,
            ApprovalDecision(
                approved=True,
                approver="Manager Sarah Johnson",
                comments="Conference attendance is valuable for professional development",
            ),
        )

        # Wait for workflow completion
        result2 = await handle.result()
        print(f"\n{result2}")

        print("\n=== Example 3: Manual Rejection ===\n")

        # Another expense that will be rejected
        request3 = ExpenseRequest(
            employee="Bob Wilson",
            amount=5000.00,
            category="Equipment",
            description="New gaming setup",
        )

        handle3 = await client.start_workflow(
            ExpenseApprovalWorkflow.run,
            request3,
            id=f"1-basic-human-in-loop-rejection-{uuid.uuid4()}",
            task_queue="1-basic-human-in-loop-task-queue",
        )

        print(f"Expense request submitted for ${request3.amount}")
        await asyncio.sleep(1)

        # Manager rejects
        await handle3.signal(
            ExpenseApprovalWorkflow.reject,
            ApprovalDecision(
                approved=False,
                approver="Manager Sarah Johnson",
                comments="Gaming setup not related to business needs",
            ),
        )

        result3 = await handle3.result()
        print(f"\n{result3}")


if __name__ == "__main__":
    asyncio.run(main())
