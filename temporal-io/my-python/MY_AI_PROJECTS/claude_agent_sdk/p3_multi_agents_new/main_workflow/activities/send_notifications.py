"""Activity 5: Send notifications via Slack."""

import logging
import os
from typing import Dict

from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def send_notifications(report: Dict) -> bool:
    """
    Activity 5: Send notifications via Slack.

    - Format comprehensive review report
    - Send to Slack channel with rich formatting
    - Include score, critical issues, and recommendations
    """
    logger.info(f"Sending Slack notification for submission: {report['submission_id']}")

    try:
        from slack_sdk.web.async_client import AsyncWebClient

        slack_token = os.getenv("SLACK_BOT_TOKEN")
        slack_channel = os.getenv("SLACK_CHANNEL", "code-reviews")

        if not slack_token:
            logger.warning("SLACK_BOT_TOKEN not set - skipping Slack notification")
            logger.info(f"Would have sent: score={report['overall_score']}, "
                       f"critical_issues={report.get('critical_security_issues', 0)}")
            return True

        client = AsyncWebClient(token=slack_token)

        # Determine score emoji and color
        score = report.get('overall_score', 0)
        if score >= 90:
            score_emoji = "🟢"
            color = "good"
        elif score >= 70:
            score_emoji = "🟡"
            color = "warning"
        else:
            score_emoji = "🔴"
            color = "danger"

        # Format priority issues
        priority_issues = report.get('priority_issues', [])
        issues_text = "\n".join(f"• {issue}" for issue in priority_issues[:5])
        if not issues_text:
            issues_text = "No critical issues found"

        # Format recommendations
        recommendations = report.get('recommendations', [])
        recs_text = "\n".join(f"• {rec}" for rec in recommendations[:5])
        if not recs_text:
            recs_text = "No specific recommendations"

        # Format test results
        test_results = report.get('test_results', {})
        test_summary = f"{test_results.get('passed', 0)}/{test_results.get('total_tests', 0)} tests passed"

        # Send formatted message to Slack
        response = await client.chat_postMessage(
            channel=slack_channel,
            text=f"Code Review Complete: {report['submission_id']} - Score: {score}/100",
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{score_emoji} Code Review Report",
                        "emoji": True
                    }
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Submission ID:*\n`{report['submission_id']}`"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Language:*\n{report.get('language', 'N/A')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Overall Score:*\n{score_emoji} *{score}/100*"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Test Coverage:*\n{report.get('test_coverage', 0):.1f}%"
                        }
                    ]
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📊 Review Summary*\n"
                               f"• Security Issues: {report.get('security_findings_count', 0)} "
                               f"({report.get('critical_security_issues', 0)} critical)\n"
                               f"• Performance Issues: {report.get('performance_bottlenecks', 0)}\n"
                               f"• Style Issues: {report.get('style_issues_count', 0)}\n"
                               f"• Tests: {test_summary}"
                    }
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🔴 Priority Issues*\n{issues_text}"
                    }
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*💡 Recommendations*\n{recs_text}"
                    }
                },
                {"type": "divider"},
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"📅 {report.get('review_date', 'N/A')} | "
                                   f"🤖 Generated by Code Review Agent"
                        }
                    ]
                }
            ],
            attachments=[
                {
                    "color": color,
                    "text": report.get('summary', 'No summary available')[:300]
                }
            ]
        )

        logger.info(f"Slack notification sent successfully. Message TS: {response['ts']}")
        return True

    except ImportError:
        logger.warning("slack_sdk not installed - skipping Slack notification")
        logger.info("Install with: uv add slack-sdk aiohttp")
        logger.info(f"Report summary: score={report['overall_score']}, "
                   f"critical_issues={report.get('critical_security_issues', 0)}")
        return True

    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")
        # Don't fail the workflow if notification fails
        logger.info(f"Report summary (notification failed): score={report['overall_score']}, "
                   f"critical_issues={report.get('critical_security_issues', 0)}")
        return False
