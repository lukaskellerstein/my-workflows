"""Activity 3: Execute generated tests using E2B Agent."""

import logging
from typing import Any, Dict

from temporalio import activity
from agents.test_executor_agent import TestExecutorAgent
from models import CodeSubmission

logger = logging.getLogger(__name__)


@activity.defn
async def execute_generated_tests(submission: CodeSubmission, test_suite_dict: Dict) -> Dict[str, Any]:
    """
    Activity 3: Execute generated tests using E2B Agent.

    Uses E2B sandbox to safely execute tests and measure coverage.

    - Run unit tests in E2B sandbox
    - Run integration tests in E2B sandbox
    - Generate coverage report
    - Compile results
    """
    logger.info("Executing generated tests using TestExecutorAgent")

    # Extract test data
    unit_tests = test_suite_dict.get("unit_tests", [])
    integration_tests = test_suite_dict.get("integration_tests", [])
    coverage_percentage = test_suite_dict.get("coverage_percentage", 75.0)

    # Use dedicated agent for test execution with original code
    agent = TestExecutorAgent()
    results = await agent.execute_tests(
        submission.code,
        submission.language,
        unit_tests,
        integration_tests,
        coverage_percentage
    )

    logger.info(
        f"Test execution complete: {results['passed']}/{results['total_tests']} passed"
    )

    return results
