"""Starter script for Code Review Pipeline."""

import asyncio
import logging
from datetime import datetime

from temporalio.client import Client
from temporalio.common import TypedSearchAttributes, SearchAttributeKey, SearchAttributePair

from shared.config import config
from models import CodeSubmission, ProgrammingLanguage

from main_workflow.workflow import CodeReviewWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define search attribute key for tagging workflows
ai_agent_type = SearchAttributeKey.for_text("AIAgentType")


async def main() -> None:
    """Start a code review workflow."""

    # Connect to Temporal server
    client = await Client.connect(config.temporal.host, namespace=config.temporal.namespace)

    # Sample code submission
    code = '''
def authenticate_user(username, password):
    """Authenticate user against database."""
    import sqlite3

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # SECURITY ISSUE: SQL injection vulnerability
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)

    user = cursor.fetchone()
    conn.close()

    return user is not None


def process_user_data(data):
    """Process user data without validation."""
    # PERFORMANCE ISSUE: O(n^2) complexity
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if i != j and data[i] > data[j]:
                result.append((data[i], data[j]))

    return result


def calculate_total(items):
    """Calculate total price."""
    # STYLE ISSUE: No type hints, unclear variable names
    t = 0
    for x in items:
        t += x['p'] * x['q']  # Poor naming
    return t
'''

    submission = CodeSubmission(
        submission_id=f"sub-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        code=code,
        language=ProgrammingLanguage.PYTHON,
        description="User authentication and data processing module",
        metadata={"project": "user-management", "priority": "high"},
    )

    # Start workflow
    workflow_id = f"code-review-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    logger.info(f"Starting code review workflow: {workflow_id}")
    logger.info(f"Submission: {submission.submission_id}")

    result = await client.execute_workflow(
        CodeReviewWorkflow.run,
        submission,
        id=workflow_id,
        task_queue="code-review-queue",
        search_attributes=TypedSearchAttributes(
            [SearchAttributePair(ai_agent_type, "ClaudeAgentSDK")]
        ),
    )

    logger.info("=" * 80)
    logger.info("CODE REVIEW COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Submission ID: {result['submission_id']}")
    logger.info(f"Overall Score: {result['overall_score']}/100")
    logger.info(f"Security Findings: {result['security_findings_count']}")
    logger.info(f"  - Critical Issues: {result['critical_security_issues']}")
    logger.info(f"Performance Bottlenecks: {result['performance_bottlenecks']}")
    logger.info(f"Style Issues: {result['style_issues_count']}")
    logger.info(f"Test Coverage: {result['test_coverage']}%")
    logger.info(f"Test Results: {result['test_results']['passed']}/{result['test_results']['total_tests']} passed")
    logger.info("")
    logger.info("Priority Issues:")
    for issue in result.get("priority_issues", [])[:5]:
        logger.info(f"  - {issue}")
    logger.info("")
    logger.info("Recommendations:")
    for rec in result.get("recommendations", [])[:5]:
        logger.info(f"  - {rec}")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
