"""Activities for Code Review Pipeline."""

import asyncio
import logging
from datetime import datetime
from typing import Dict

from temporalio import activity

from shared.models import CodeSubmission, ProgrammingLanguage

from .agent_team_sdk import CodeReviewTeam

logger = logging.getLogger(__name__)


@activity.defn
async def validate_code_submission(submission: CodeSubmission) -> Dict[str, bool]:
    """
    Activity 1: Validate code submission (Deterministic).

    - Validate file format
    - Check code length
    - Verify metadata
    """
    logger.info(f"Validating code submission: {submission.submission_id}")

    is_valid = True
    errors = []

    # Check language is supported
    if submission.language not in [lang.value for lang in ProgrammingLanguage]:
        errors.append(f"Unsupported language: {submission.language}")
        is_valid = False

    # Check code length (not empty, not too large)
    if len(submission.code) < 10:
        errors.append("Code too short (minimum 10 characters)")
        is_valid = False
    elif len(submission.code) > 100000:
        errors.append("Code too large (maximum 100,000 characters)")
        is_valid = False

    # Check description
    if not submission.description or len(submission.description) < 5:
        errors.append("Description too short (minimum 5 characters)")
        is_valid = False

    result = {"is_valid": is_valid, "errors": errors}

    logger.info(f"Validation result: {'valid' if is_valid else 'invalid'}")
    return result


@activity.defn
async def multi_agent_code_review(submission: CodeSubmission) -> Dict:
    """
    Activity 2: Multi-agent code review (Team of AI Agents - Supervision Pattern).

    Coordinates:
    - Security Agent (with E2B)
    - Performance Agent (with E2B)
    - Style Agent (with Academia)
    - Test Agent (with E2B)
    - Supervisor Agent (coordinates all)
    """
    logger.info(f"Starting multi-agent review for: {submission.submission_id}")

    # Create code review team
    team = CodeReviewTeam()

    # Execute team review
    report = await team.review(submission)

    logger.info(f"Multi-agent review complete: {report['overall_score']} score")
    return report


@activity.defn
async def execute_generated_tests(test_suite_dict: Dict) -> Dict[str, any]:
    """
    Activity 3: Execute generated tests (Deterministic).

    - Run unit tests
    - Run integration tests
    - Generate coverage report
    - Compile results
    """
    logger.info("Executing generated tests")

    # Simulate test execution
    # In production, this would use E2B to safely execute tests

    await asyncio.sleep(1)  # Simulate test execution time

    # Simulate results
    unit_test_count = len(test_suite_dict.get("unit_tests", []))
    integration_test_count = len(test_suite_dict.get("integration_tests", []))

    results = {
        "total_tests": unit_test_count + integration_test_count,
        "passed": unit_test_count + integration_test_count - 1,  # 1 simulated failure
        "failed": 1,
        "coverage_percentage": test_suite_dict.get("coverage_percentage", 0.0),
        "execution_time_seconds": 1.5,
    }

    logger.info(
        f"Test execution complete: {results['passed']}/{results['total_tests']} passed"
    )
    return results


@activity.defn
async def generate_review_report(
    submission: CodeSubmission, review_report: Dict, test_results: Dict
) -> Dict:
    """
    Activity 4: Generate final review report (AI Agent with Mem0).

    Uses past reviews to:
    - Contextualize findings
    - Generate recommendations
    - Create priority list
    """
    logger.info("Generating final review report")

    # Combine all information
    final_report = {
        "submission_id": submission.submission_id,
        "language": submission.language,
        "description": submission.description,
        "review_date": datetime.now().isoformat(),
        "overall_score": review_report["overall_score"],
        "security_findings_count": len(review_report["security_findings"]),
        "critical_security_issues": sum(
            1
            for f in review_report["security_findings"]
            if f["severity"] == "critical"
        ),
        "performance_bottlenecks": len(
            review_report["performance_analysis"]["bottlenecks"]
        ),
        "style_issues_count": len(review_report["style_issues"]),
        "test_coverage": review_report["test_suite"]["coverage_percentage"],
        "test_results": test_results,
        "priority_issues": review_report["priority_issues"],
        "recommendations": review_report["recommendations"],
        "summary": review_report["summary"],
    }

    logger.info(f"Final report generated for: {submission.submission_id}")
    return final_report


@activity.defn
async def send_notifications(report: Dict) -> bool:
    """
    Activity 5: Send notifications (Deterministic).

    - Format report
    - Send to stakeholders
    - Update project management tools
    """
    logger.info(f"Sending notifications for submission: {report['submission_id']}")

    # Simulate notification sending
    await asyncio.sleep(0.2)

    logger.info(
        f"Notifications sent: score={report['overall_score']}, "
        f"critical_issues={report['critical_security_issues']}"
    )

    return True
