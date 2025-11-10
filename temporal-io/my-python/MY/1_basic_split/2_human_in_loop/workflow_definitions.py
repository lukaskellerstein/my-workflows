"""
Workflow and Activity Definitions - Human in the Loop
Demonstrates workflows that require human approval or decision-making.
The workflow pauses and waits for human input via signals.
"""
import asyncio
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from temporalio import activity, workflow


class ApprovalStatus(str, Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


@dataclass
class ExpenseRequest:
    """Represents an expense approval request."""

    employee: str
    amount: float
    category: str
    description: str


@dataclass
class ApprovalDecision:
    """Represents an approval or rejection decision."""

    approved: bool
    approver: str
    comments: str


@dataclass
class EmployeeNotification:
    """Notification to send to employee."""

    request: ExpenseRequest
    status: str  # Store as string instead of enum


# Activities


@activity.defn
def validate_expense(request: ExpenseRequest) -> bool:
    """Validate expense request against business rules."""
    activity.logger.info(f"Validating expense request from {request.employee}")
    # Validate expense rules
    if request.amount <= 0:
        return False
    if request.amount > 100000:  # Max limit
        return False
    return True


@activity.defn
def notify_approver(request: ExpenseRequest) -> str:
    """Notify approver about pending expense request."""
    activity.logger.info(
        f"Notifying approver about ${request.amount} expense from {request.employee}"
    )
    # In real scenario: send email, Slack message, etc.
    return f"Notification sent to approver for {request.employee}'s expense"


@activity.defn
def process_approved_expense(request: ExpenseRequest) -> str:
    """Process an approved expense."""
    activity.logger.info(f"Processing approved expense of ${request.amount}")
    # In real scenario: update accounting system, trigger payment
    return f"Expense of ${request.amount} processed for {request.employee}"


@activity.defn
def notify_employee(notification: EmployeeNotification) -> str:
    """Notify employee about expense decision."""
    activity.logger.info(
        f"Notifying {notification.request.employee} about {notification.status} expense"
    )
    # In real scenario: send email to employee
    return f"Employee {notification.request.employee} notified: {notification.status}"


# Workflow with human approval


@workflow.defn
class ExpenseApprovalWorkflow:
    """
    Workflow that handles expense approval with human intervention.

    Uses signals to receive approval/rejection decisions from humans.
    Implements timeout for approval decisions.
    """

    def __init__(self) -> None:
        self._approval_status = ApprovalStatus.PENDING
        self._approval_decision: ApprovalDecision | None = None

    @workflow.run
    async def run(self, request: ExpenseRequest) -> str:
        """Execute expense approval workflow."""
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
        """Signal sent by approver to approve the expense."""
        workflow.logger.info(f"Approval received from {decision.approver}")
        self._approval_status = ApprovalStatus.APPROVED
        self._approval_decision = decision

    @workflow.signal
    async def reject(self, decision: ApprovalDecision) -> None:
        """Signal sent by approver to reject the expense."""
        workflow.logger.info(f"Rejection received from {decision.approver}")
        self._approval_status = ApprovalStatus.REJECTED
        self._approval_decision = decision

    @workflow.query
    def get_status(self) -> str:
        """Query to check current approval status."""
        return self._approval_status.value

    @workflow.query
    def get_approval_decision(self) -> ApprovalDecision | None:
        """Query to get the approval decision if available."""
        return self._approval_decision
