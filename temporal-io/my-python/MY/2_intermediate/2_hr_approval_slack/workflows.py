"""HR approval workflow demonstrating Temporal Updates."""

from datetime import datetime, timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from models import (
        ApprovalDecision,
        ApprovalRequest,
        ApprovalState,
        ApprovalStatus,
    )
    from activities import (
        send_slack_notification,
        send_approval_notification,
        notify_employee,
        record_approval,
        provision_resource,
    )


@workflow.defn
class HRApprovalWorkflow:
    """
    HR approval workflow demonstrating Temporal Updates.

    Updates combine the benefits of Signals and Queries:
    - Send data into the workflow (like Signal)
    - Return data from the workflow (like Query)
    - Atomic operations with validation

    Updates:
    - submit_manager_approval: Manager submits approval/rejection
    - submit_hr_approval: HR submits final approval/rejection
    - add_comments: Add comments without changing status

    Signals:
    - cancel_request: Cancel the request

    Queries:
    - get_status: Get current status
    - get_full_state: Get complete state
    """

    def __init__(self) -> None:
        """Initialize workflow state."""
        self._request: ApprovalRequest | None = None
        self._status = ApprovalStatus.PENDING
        self._manager_decision: ApprovalDecision | None = None
        self._hr_decision: ApprovalDecision | None = None
        self._created_at: datetime | None = None
        self._updated_at: datetime | None = None
        self._completed_at: datetime | None = None
        self._cancellation_reason: str | None = None

        # Control flags
        self._manager_responded = False
        self._hr_responded = False
        self._should_cancel = False

    @workflow.run
    async def run(self, request: ApprovalRequest) -> ApprovalState:
        """Main workflow execution."""
        self._request = request
        self._created_at = workflow.now()
        self._updated_at = workflow.now()

        workflow.logger.info(f"Starting approval workflow for {request.request_id}")

        try:
            # Step 1: Send initial notification to manager
            workflow.logger.info("Step 1: Notifying manager...")
            await workflow.execute_activity(
                send_slack_notification,
                args=[request, "Manager", "🔔 New approval request"],
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Step 2: Wait for manager approval (UPDATE)
            workflow.logger.info("Step 2: Waiting for manager approval...")
            await workflow.wait_condition(
                lambda: self._manager_responded or self._should_cancel,
                timeout=timedelta(hours=48)
            )

            if self._should_cancel:
                return await self._handle_cancellation()

            # Check if manager approved
            if not self._manager_decision.approved:
                workflow.logger.info("Manager rejected the request")
                self._status = ApprovalStatus.REJECTED
                self._completed_at = workflow.now()

                await workflow.execute_activity(
                    notify_employee,
                    args=[
                        request,
                        "REJECTED",
                        f"Your request was rejected by manager. "
                        f"Reason: {self._manager_decision.comments}"
                    ],
                    start_to_close_timeout=timedelta(seconds=30),
                )

                return self._get_current_state()

            # Manager approved
            workflow.logger.info("Manager approved the request")
            self._status = ApprovalStatus.MANAGER_APPROVED
            self._updated_at = workflow.now()

            # Step 3: Send notification to HR
            workflow.logger.info("Step 3: Notifying HR...")
            await workflow.execute_activity(
                send_slack_notification,
                args=[request, "HR Team", "✅ Manager approved, awaiting HR review"],
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Step 4: Wait for HR approval (UPDATE)
            workflow.logger.info("Step 4: Waiting for HR approval...")
            await workflow.wait_condition(
                lambda: self._hr_responded or self._should_cancel,
                timeout=timedelta(hours=72)
            )

            if self._should_cancel:
                return await self._handle_cancellation()

            # Record HR decision
            await workflow.execute_activity(
                record_approval,
                args=[request.request_id, self._hr_decision],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            # Check if HR approved
            if not self._hr_decision.approved:
                workflow.logger.info("HR rejected the request")
                self._status = ApprovalStatus.REJECTED
                self._completed_at = workflow.now()

                await workflow.execute_activity(
                    notify_employee,
                    args=[
                        request,
                        "REJECTED",
                        f"Your request was rejected by HR. "
                        f"Reason: {self._hr_decision.comments}"
                    ],
                    start_to_close_timeout=timedelta(seconds=30),
                )

                return self._get_current_state()

            # HR approved - fully approved!
            workflow.logger.info("HR approved - request fully approved!")
            self._status = ApprovalStatus.HR_APPROVED
            self._completed_at = workflow.now()
            self._updated_at = workflow.now()

            # Step 5: Provision the resource
            workflow.logger.info("Step 5: Provisioning resource...")
            provision_result = await workflow.execute_activity(
                provision_resource,
                request,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            # Notify employee of approval
            await workflow.execute_activity(
                notify_employee,
                args=[
                    request,
                    "APPROVED",
                    f"Your request has been fully approved! {provision_result}"
                ],
                start_to_close_timeout=timedelta(seconds=30),
            )

            workflow.logger.info(
                f"Approval workflow completed successfully for {request.request_id}"
            )

            return self._get_current_state()

        except Exception as e:
            workflow.logger.error(f"Approval workflow failed: {e}")
            self._status = ApprovalStatus.CANCELLED
            self._cancellation_reason = f"System error: {str(e)}"
            self._completed_at = workflow.now()
            raise

    async def _handle_cancellation(self) -> ApprovalState:
        """Handle request cancellation."""
        workflow.logger.info(
            f"Cancelling request {self._request.request_id}: "
            f"{self._cancellation_reason}"
        )

        await workflow.execute_activity(
            notify_employee,
            args=[
                self._request,
                "CANCELLED",
                f"Your request was cancelled. Reason: {self._cancellation_reason}"
            ],
            start_to_close_timeout=timedelta(seconds=30),
        )

        self._status = ApprovalStatus.CANCELLED
        self._completed_at = workflow.now()

        return self._get_current_state()

    # UPDATES - Send data in AND get data back (with validation)

    @workflow.update
    def submit_manager_approval(self, decision: ApprovalDecision) -> ApprovalState:
        """
        Update: Manager submits approval decision.

        This demonstrates the UPDATE pattern:
        1. Receives approval decision (input)
        2. Validates the decision
        3. Updates workflow state
        4. Returns updated state (output)
        """
        workflow.logger.info(
            f"Manager approval received: "
            f"{'Approved' if decision.approved else 'Rejected'} by {decision.approver_name}"
        )

        self._manager_decision = decision
        self._manager_responded = True
        self._updated_at = workflow.now()

        # Send notification activity (async)
        workflow.start_activity(
            send_approval_notification,
            args=[self._request, decision, False],
            start_to_close_timeout=timedelta(seconds=30),
        )

        return self._get_current_state()

    @workflow.update(name="submit_manager_approval")
    def validate_manager_approval(self, decision: ApprovalDecision) -> None:
        """
        Validator for manager approval update.

        Validators run BEFORE the update handler and can reject invalid updates.
        """
        if self._status != ApprovalStatus.PENDING:
            raise ApplicationError(
                f"Cannot submit manager approval. Current status: {self._status.value}",
                non_retryable=True
            )

        if self._manager_responded:
            raise ApplicationError(
                "Manager has already submitted approval",
                non_retryable=True
            )

    @workflow.update
    def submit_hr_approval(self, decision: ApprovalDecision) -> ApprovalState:
        """
        Update: HR submits final approval decision.

        Returns the updated state after HR decision.
        """
        workflow.logger.info(
            f"HR approval received: "
            f"{'Approved' if decision.approved else 'Rejected'} by {decision.approver_name}"
        )

        self._hr_decision = decision
        self._hr_responded = True
        self._updated_at = workflow.now()

        # Send notification activity (async)
        workflow.start_activity(
            send_approval_notification,
            args=[self._request, decision, True],
            start_to_close_timeout=timedelta(seconds=30),
        )

        return self._get_current_state()

    @workflow.update(name="submit_hr_approval")
    def validate_hr_approval(self, decision: ApprovalDecision) -> None:
        """Validator for HR approval update."""
        if self._status != ApprovalStatus.MANAGER_APPROVED:
            raise ApplicationError(
                f"Cannot submit HR approval. Current status: {self._status.value}. "
                f"Manager must approve first.",
                non_retryable=True
            )

        if self._hr_responded:
            raise ApplicationError(
                "HR has already submitted approval",
                non_retryable=True
            )

    @workflow.update
    def add_comments(self, commenter_name: str, comments: str) -> str:
        """
        Update: Add comments without changing approval status.

        Demonstrates lightweight updates that don't affect workflow logic.
        """
        workflow.logger.info(f"Comments added by {commenter_name}: {comments}")

        self._updated_at = workflow.now()

        return f"Comments added successfully by {commenter_name} at {self._updated_at}"

    # SIGNAL - One-way message (no return value)

    @workflow.signal
    def cancel_request(self, reason: str) -> None:
        """Signal: Cancel the approval request."""
        workflow.logger.info(f"Cancellation requested: {reason}")
        self._cancellation_reason = reason
        self._should_cancel = True
        self._updated_at = workflow.now()

    # QUERIES - Read-only access to state

    @workflow.query
    def get_status(self) -> str:
        """Query: Get current approval status."""
        return self._status.value

    @workflow.query
    def get_full_state(self) -> ApprovalState:
        """Query: Get complete approval state."""
        return self._get_current_state()

    def _get_current_state(self) -> ApprovalState:
        """Build current approval state."""
        return ApprovalState(
            request_id=self._request.request_id,
            employee_id=self._request.employee_id,
            employee_name=self._request.employee_name,
            request_type=self._request.request_type,
            title=self._request.title,
            description=self._request.description,
            priority=self._request.priority,
            status=self._status,
            manager_decision=self._manager_decision,
            hr_decision=self._hr_decision,
            created_at=self._created_at,
            updated_at=self._updated_at,
            completed_at=self._completed_at,
            cancellation_reason=self._cancellation_reason,
        )
