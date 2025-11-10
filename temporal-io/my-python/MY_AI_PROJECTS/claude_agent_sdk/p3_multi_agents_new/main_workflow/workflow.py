"""Workflow for Code Review Pipeline."""

import logging
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from models import CodeSubmission

from .activities import (
    execute_generated_tests,
    generate_review_report,
    multi_agent_code_review,
    send_notifications,
    validate_code_submission,
)

logger = logging.getLogger(__name__)


@workflow.defn
class CodeReviewWorkflow:
    """
    Workflow orchestrating the code review pipeline with multi-agent teams.

    Steps:
    1. Validate submission (Deterministic)
    2. Multi-agent code review (Team - Supervision Pattern)
    3. Execute tests (Deterministic)
    4. Generate report (AI Agent + Mem0)
    5. Send notifications (Deterministic)
    """

    @workflow.run
    async def run(self, submission: CodeSubmission) -> dict:
        """Execute the code review workflow."""

        workflow.logger.info(
            f"Starting code review workflow for: {submission.submission_id}"
        )

        # Step 1: Validate submission
        validation_result = await workflow.execute_activity(
            validate_code_submission,
            submission,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not validation_result["is_valid"]:
            error_msg = f"Validation failed: {', '.join(validation_result['errors'])}"
            workflow.logger.error(error_msg)
            raise ValueError(error_msg)

        workflow.logger.info("Code submission validated")

        # Step 2: Multi-agent code review
        agent_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=60),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        review_report = await workflow.execute_activity(
            multi_agent_code_review,
            submission,
            start_to_close_timeout=timedelta(
                seconds=600
            ),  # 10 minutes for multi-agent coordination
            retry_policy=agent_retry_policy,
        )

        workflow.logger.info(
            f"Multi-agent review complete: {review_report['overall_score']} score"
        )

        # Step 3: Execute generated tests
        test_results = await workflow.execute_activity(
            execute_generated_tests,
            args=[submission, review_report["test_suite"]],
            start_to_close_timeout=timedelta(seconds=240),
        )

        workflow.logger.info(
            f"Tests executed: {test_results['passed']}/{test_results['total_tests']} passed"
        )

        # Step 4: Generate final report
        final_report = await workflow.execute_activity(
            generate_review_report,
            args=[submission, review_report, test_results],
            start_to_close_timeout=timedelta(seconds=240),
            retry_policy=agent_retry_policy,
        )

        workflow.logger.info("Final report generated")

        # Step 5: Send notifications
        await workflow.execute_activity(
            send_notifications,
            final_report,
            start_to_close_timeout=timedelta(seconds=180),
        )

        workflow.logger.info("Notifications sent")

        return final_report
