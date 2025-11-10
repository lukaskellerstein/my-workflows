"""Activities for HR approval workflow."""

import asyncio
import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from slack_sdk.web.async_client import AsyncWebClient
from temporalio import activity

from models import ApprovalDecision, ApprovalRequest, RequestType

# Load environment variables
load_dotenv()

# Initialize Slack client
slack_client = AsyncWebClient(token=os.getenv("SLACK_BOT_TOKEN"))
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL_ID", "general")


def _format_request_message(request: ApprovalRequest) -> str:
    """Format request details for Slack message."""
    msg = f"""
*New {request.request_type.value.replace('_', ' ').title()} Request*

*Request ID:* {request.request_id}
*Employee:* {request.employee_name} ({request.employee_id})
*Title:* {request.title}
*Priority:* {request.priority.value.upper()}
*Description:* {request.description}
"""

    if request.amount:
        msg += f"\n*Amount:* ${request.amount:.2f}"

    if request.start_date and request.end_date:
        msg += f"\n*Period:* {request.start_date.strftime('%Y-%m-%d')} to {request.end_date.strftime('%Y-%m-%d')}"

    return msg


@activity.defn
async def send_slack_notification(
    request: ApprovalRequest,
    approver_name: str,
    message: str
) -> str:
    """Send notification to Slack channel."""
    activity.logger.info(f"Sending Slack notification for {request.request_id}")

    try:
        formatted_message = f"""
{message}

{_format_request_message(request)}

*Awaiting approval from:* {approver_name}
"""

        # For demo purposes, we'll just log the message
        # In production, you would actually send to Slack:
        # response = await slack_client.chat_postMessage(
        #     channel=SLACK_CHANNEL,
        #     text=formatted_message,
        #     blocks=[
        #         {
        #             "type": "section",
        #             "text": {"type": "mrkdwn", "text": formatted_message}
        #         }
        #     ]
        # )
        # return response["ts"]

        activity.logger.info(f"Slack message:\n{formatted_message}")

        # Return mock message ID
        return f"MOCK-MSG-{request.request_id}-{datetime.now().timestamp()}"

    except Exception as e:
        activity.logger.error(f"Failed to send Slack notification: {e}")
        # In a real system, you might want to retry or handle this differently
        return f"FAILED-{request.request_id}"


@activity.defn
async def send_approval_notification(
    request: ApprovalRequest,
    decision: ApprovalDecision,
    is_final: bool
) -> None:
    """Send approval decision notification."""
    activity.logger.info(
        f"Sending approval notification for {request.request_id}: "
        f"{'Approved' if decision.approved else 'Rejected'} by {decision.approver_name}"
    )

    status = "✅ APPROVED" if decision.approved else "❌ REJECTED"
    final_msg = " (FINAL)" if is_final else ""

    message = f"""
*{status}{final_msg}*

*Request:* {request.title}
*Approver:* {decision.approver_name}
*Comments:* {decision.comments}
*Time:* {decision.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""

    activity.logger.info(f"Approval notification:\n{message}")

    # In production, send to Slack
    await asyncio.sleep(0.5)


@activity.defn
async def notify_employee(
    request: ApprovalRequest,
    status: str,
    message: str
) -> None:
    """Notify employee about request status."""
    activity.logger.info(
        f"Notifying employee {request.employee_name} about {request.request_id}: {status}"
    )

    notification = f"""
*Status Update for Your Request*

*Request:* {request.title}
*Status:* {status}
*Message:* {message}

*Request ID:* {request.request_id}
"""

    activity.logger.info(f"Employee notification:\n{notification}")

    # In production, send email or Slack DM
    await asyncio.sleep(0.5)


@activity.defn
async def record_approval(
    request_id: str,
    decision: ApprovalDecision
) -> None:
    """Record approval in HR system."""
    activity.logger.info(
        f"Recording approval decision for {request_id} in HR system"
    )

    # Simulate database write
    await asyncio.sleep(1)

    activity.logger.info(
        f"Approval recorded: {request_id} - "
        f"{'Approved' if decision.approved else 'Rejected'} by {decision.approver_name}"
    )


@activity.defn
async def provision_resource(request: ApprovalRequest) -> str:
    """Provision requested resource (equipment, time off, etc)."""
    activity.logger.info(
        f"Provisioning resource for {request.request_id}: {request.request_type.value}"
    )

    # Simulate resource provisioning based on type
    await asyncio.sleep(2)

    if request.request_type == RequestType.TIME_OFF:
        result = f"Calendar updated: {request.start_date} to {request.end_date}"
    elif request.request_type == RequestType.EQUIPMENT_REQUEST:
        result = f"Equipment order placed: {request.description}"
    elif request.request_type == RequestType.EXPENSE_REIMBURSEMENT:
        result = f"Reimbursement processed: ${request.amount}"
    elif request.request_type == RequestType.PROMOTION:
        result = f"HR records updated: {request.description}"
    else:
        result = f"Request processed: {request.title}"

    activity.logger.info(f"Resource provisioned: {result}")

    return result
