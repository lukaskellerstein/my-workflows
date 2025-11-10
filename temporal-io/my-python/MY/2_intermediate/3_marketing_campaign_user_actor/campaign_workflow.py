"""Campaign workflow - sends messages to multiple users via User Actors."""

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from models import CampaignMessage, CampaignType, FrequencyCheckResult
    from activities import send_message, log_analytics_event
    from user_actor_workflow import UserActorWorkflow


@workflow.defn
class CampaignWorkflow:
    """
    Campaign workflow that sends messages to users.

    This workflow:
    1. Queries UserActorWorkflow to check if message can be sent (frequency cap)
    2. If allowed, sends the message via activity
    3. Signals UserActorWorkflow to record the message was sent

    Key Pattern:
    - Does NOT maintain user state itself
    - Delegates to User Actor for all user-specific state
    - Can run concurrently with other campaigns for same user
    - User Actor ensures frequency caps are respected across ALL campaigns
    """

    def __init__(self) -> None:
        """Initialize campaign state."""
        self._message: CampaignMessage | None = None
        self._users_targeted = 0
        self._users_sent = 0
        self._users_skipped = 0

    @workflow.run
    async def run(
        self,
        message: CampaignMessage,
        target_user_ids: list[str]
    ) -> dict:
        """
        Run campaign to send messages to target users.

        For each user:
        1. Check with User Actor if we can send
        2. If yes, send message and record in User Actor
        3. If no, skip and log reason
        """
        self._message = message
        self._users_targeted = len(target_user_ids)

        workflow.logger.info(
            f"🚀 Starting campaign: {message.campaign_name} "
            f"({message.campaign_type.value}) - "
            f"Targeting {len(target_user_ids)} users"
        )

        results = []

        for user_id in target_user_ids:
            result = await self._send_to_user(user_id, message)
            results.append(result)

            if result["sent"]:
                self._users_sent += 1
            else:
                self._users_skipped += 1

        workflow.logger.info(
            f"✅ Campaign complete: {message.campaign_name} - "
            f"Sent: {self._users_sent}, Skipped: {self._users_skipped}"
        )

        # Log campaign completion analytics
        await workflow.execute_activity(
            log_analytics_event,
            args=[
                "campaign-system",
                "campaign_completed",
                message.campaign_id,
                {
                    "campaign_name": message.campaign_name,
                    "users_targeted": self._users_targeted,
                    "users_sent": self._users_sent,
                    "users_skipped": self._users_skipped,
                }
            ],
            start_to_close_timeout=timedelta(seconds=10),
        )

        return {
            "campaign_id": message.campaign_id,
            "campaign_name": message.campaign_name,
            "users_targeted": self._users_targeted,
            "users_sent": self._users_sent,
            "users_skipped": self._users_skipped,
            "results": results,
        }

    async def _send_to_user(
        self,
        user_id: str,
        message: CampaignMessage
    ) -> dict:
        """
        Send message to a single user via User Actor pattern.

        Steps:
        1. Get User Actor workflow handle
        2. Query: Can we send? (frequency check)
        3. If yes: Send message + Signal User Actor to record it
        4. If no: Skip and log reason
        """
        # Get User Actor workflow handle
        user_actor_workflow_id = f"user-actor-{user_id}"
        user_actor_handle = workflow.get_external_workflow_handle(
            user_actor_workflow_id
        )

        try:
            # QUERY User Actor: Can we send this message?
            frequency_check: FrequencyCheckResult = await user_actor_handle.query(
                UserActorWorkflow.can_send_message,
                message
            )

            if not frequency_check.allowed:
                # Frequency cap hit - skip this user
                workflow.logger.info(
                    f"⏭️  Skipping user {user_id}: {frequency_check.reason}"
                )

                await workflow.execute_activity(
                    log_analytics_event,
                    args=[
                        user_id,
                        "message_skipped",
                        message.campaign_id,
                        {
                            "reason": frequency_check.reason,
                            "messages_today": frequency_check.messages_sent_today,
                            "messages_week": frequency_check.messages_sent_this_week,
                        }
                    ],
                    start_to_close_timeout=timedelta(seconds=10),
                )

                return {
                    "user_id": user_id,
                    "sent": False,
                    "reason": frequency_check.reason,
                    "frequency_check": {
                        "messages_today": frequency_check.messages_sent_today,
                        "messages_this_week": frequency_check.messages_sent_this_week,
                        "messages_this_month": frequency_check.messages_sent_this_month,
                    }
                }

            # Allowed to send - send the message!
            workflow.logger.info(
                f"📤 Sending to user {user_id}: {message.campaign_name}"
            )

            success = await workflow.execute_activity(
                send_message,
                args=[user_id, message],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            # SIGNAL User Actor: Record that message was sent
            await user_actor_handle.signal(
                UserActorWorkflow.record_message_sent,
                message,
                success
            )

            workflow.logger.info(f"✅ Sent to user {user_id}: {message.campaign_name}")

            await workflow.execute_activity(
                log_analytics_event,
                args=[
                    user_id,
                    "message_sent",
                    message.campaign_id,
                    {
                        "campaign_name": message.campaign_name,
                        "campaign_type": message.campaign_type.value,
                        "success": success,
                    }
                ],
                start_to_close_timeout=timedelta(seconds=10),
            )

            return {
                "user_id": user_id,
                "sent": True,
                "success": success,
                "frequency_check": {
                    "messages_today": frequency_check.messages_sent_today,
                    "messages_this_week": frequency_check.messages_sent_this_week,
                    "messages_this_month": frequency_check.messages_sent_this_month,
                }
            }

        except Exception as e:
            workflow.logger.error(f"❌ Error sending to user {user_id}: {e}")

            return {
                "user_id": user_id,
                "sent": False,
                "reason": f"Error: {str(e)}"
            }

    # QUERIES

    @workflow.query
    def get_progress(self) -> dict:
        """Query: Get campaign progress."""
        return {
            "campaign_id": self._message.campaign_id if self._message else None,
            "campaign_name": self._message.campaign_name if self._message else None,
            "users_targeted": self._users_targeted,
            "users_sent": self._users_sent,
            "users_skipped": self._users_skipped,
        }
