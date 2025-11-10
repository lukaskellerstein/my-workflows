"""Activity 4: Generate final review report using LLM with Mem0."""

import logging
from typing import Dict

from temporalio import activity

from models import CodeSubmission
from agents.report_generator_agent import ReportGeneratorAgent

logger = logging.getLogger(__name__)


@activity.defn
async def generate_review_report(
    submission: CodeSubmission, review_report: Dict, test_results: Dict
) -> Dict:
    """
    Activity 4: Generate final review report using LLM with Mem0.

    Uses past reviews (via Mem0) to:
    - Contextualize findings with historical data
    - Generate actionable recommendations
    - Create priority list based on severity and impact
    - Provide insights from similar past reviews
    """
    logger.info("Generating final review report with ReportGeneratorAgent")

    # Use dedicated agent for report generation
    agent = ReportGeneratorAgent()
    final_report = await agent.generate_report(submission, review_report, test_results)

    logger.info(f"Final report generated for: {submission.submission_id}")

    return final_report
