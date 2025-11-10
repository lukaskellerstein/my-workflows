"""Activity 2: Multi-agent code review (Team of AI Agents - Supervision Pattern)."""

import logging
from typing import Dict

from temporalio import activity

from models import CodeSubmission
from agents.code_review_team import CodeReviewTeam

logger = logging.getLogger(__name__)


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
