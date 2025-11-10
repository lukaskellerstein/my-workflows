"""Activities for marketing campaigns."""

import asyncio
from temporalio import activity

from models import CampaignMessage, CampaignType


@activity.defn
async def send_email(user_id: str, message: CampaignMessage) -> bool:
    """Send email to user."""
    activity.logger.info(
        f"📧 Sending email to user {user_id} - Campaign: {message.campaign_name}"
    )
    activity.logger.info(f"Content: {message.message_content}")

    # Simulate email sending
    await asyncio.sleep(1)

    activity.logger.info(f"✅ Email sent successfully to {user_id}")
    return True


@activity.defn
async def send_sms(user_id: str, message: CampaignMessage) -> bool:
    """Send SMS to user."""
    activity.logger.info(
        f"📱 Sending SMS to user {user_id} - Campaign: {message.campaign_name}"
    )
    activity.logger.info(f"Content: {message.message_content}")

    # Simulate SMS sending
    await asyncio.sleep(0.5)

    activity.logger.info(f"✅ SMS sent successfully to {user_id}")
    return True


@activity.defn
async def send_push_notification(user_id: str, message: CampaignMessage) -> bool:
    """Send push notification to user."""
    activity.logger.info(
        f"🔔 Sending push notification to user {user_id} - Campaign: {message.campaign_name}"
    )
    activity.logger.info(f"Content: {message.message_content}")

    # Simulate push notification
    await asyncio.sleep(0.3)

    activity.logger.info(f"✅ Push notification sent to {user_id}")
    return True


@activity.defn
async def send_in_app_message(user_id: str, message: CampaignMessage) -> bool:
    """Send in-app message to user."""
    activity.logger.info(
        f"💬 Sending in-app message to user {user_id} - Campaign: {message.campaign_name}"
    )
    activity.logger.info(f"Content: {message.message_content}")

    # Simulate in-app message
    await asyncio.sleep(0.2)

    activity.logger.info(f"✅ In-app message sent to {user_id}")
    return True


async def send_message(user_id: str, message: CampaignMessage) -> bool:
    """Route message to appropriate sender based on type."""
    if message.campaign_type == CampaignType.EMAIL:
        return await send_email(user_id, message)
    elif message.campaign_type == CampaignType.SMS:
        return await send_sms(user_id, message)
    elif message.campaign_type == CampaignType.PUSH_NOTIFICATION:
        return await send_push_notification(user_id, message)
    elif message.campaign_type == CampaignType.IN_APP_MESSAGE:
        return await send_in_app_message(user_id, message)
    else:
        activity.logger.error(f"Unknown campaign type: {message.campaign_type}")
        return False


@activity.defn
async def log_analytics_event(
    user_id: str,
    event_type: str,
    campaign_id: str,
    metadata: dict
) -> None:
    """Log analytics event."""
    activity.logger.info(
        f"📊 Analytics: User {user_id} - Event: {event_type} - Campaign: {campaign_id}"
    )
    activity.logger.info(f"Metadata: {metadata}")

    # Simulate analytics logging
    await asyncio.sleep(0.1)
