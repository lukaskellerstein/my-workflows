"""User Actor workflow - maintains shared state for a single user."""

from datetime import datetime, timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from models import (
        CampaignMessage,
        CampaignType,
        FrequencyCap,
        FrequencyCheckResult,
        MessageAttempt,
        UserState,
    )


@workflow.defn
class UserActorWorkflow:
    """
    User Actor pattern - long-running workflow per user.

    This workflow maintains ALL state for a single user across ALL campaigns:
    - Message frequency tracking
    - Opt-out preferences
    - Message history
    - Channel preferences

    Multiple campaign workflows signal THIS workflow to:
    - Check if they can send a message (frequency cap)
    - Record when a message was sent
    - Check user preferences

    Key Pattern:
    - WorkflowID: "user-actor-{user_id}"
    - Runs indefinitely (Continue-As-New after 30 days)
    - Single source of truth for user state
    - Scales to millions of concurrent users
    """

    def __init__(self) -> None:
        """Initialize user actor state."""
        self._user_id: str | None = None
        self._state = UserState(user_id="")
        self._frequency_cap = FrequencyCap()

        # Continue-As-New counter
        self._days_running = 0

    @workflow.run
    async def run(self, user_id: str, frequency_cap: FrequencyCap | None = None) -> None:
        """
        Main workflow - runs indefinitely.

        This is a long-running workflow that never completes normally.
        It responds to signals and queries from campaign workflows.
        """
        self._user_id = user_id
        self._state.user_id = user_id

        if frequency_cap:
            self._frequency_cap = frequency_cap

        workflow.logger.info(f"👤 User Actor started for user: {user_id}")
        workflow.logger.info(f"Frequency cap: {self._frequency_cap.max_messages_per_day}/day")

        start_time = workflow.now()

        # Run indefinitely, responding to signals and queries
        while True:
            # Sleep for 1 day
            await workflow.sleep(timedelta(days=1))

            self._days_running += 1

            # Continue-As-New every 30 days to prevent history from growing too large
            if self._days_running >= 30:
                workflow.logger.info(
                    f"User actor for {user_id} running for 30 days. "
                    f"Using Continue-As-New..."
                )
                workflow.continue_as_new(user_id, self._frequency_cap)

    # QUERIES - Read user state (called by campaign workflows)

    @workflow.query
    def get_user_state(self) -> UserState:
        """Query: Get complete user state."""
        return self._state

    @workflow.query
    def can_send_message(self, message: CampaignMessage) -> FrequencyCheckResult:
        """
        Query: Check if message can be sent based on frequency caps.

        This is the KEY QUERY that campaign workflows use before sending.
        """
        now = workflow.now()

        # Check if opted out of this channel
        if message.campaign_type in self._state.opted_out_channels:
            return FrequencyCheckResult(
                allowed=False,
                reason=f"User opted out of {message.campaign_type.value}"
            )

        # Calculate time windows
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Count messages in each window
        messages_today = sum(
            1 for attempt in self._state.message_history
            if attempt.timestamp >= day_ago and attempt.success
        )

        messages_this_week = sum(
            1 for attempt in self._state.message_history
            if attempt.timestamp >= week_ago and attempt.success
        )

        messages_this_month = sum(
            1 for attempt in self._state.message_history
            if attempt.timestamp >= month_ago and attempt.success
        )

        # Check daily cap
        if messages_today >= self._frequency_cap.max_messages_per_day:
            return FrequencyCheckResult(
                allowed=False,
                reason=f"Daily cap reached: {messages_today}/{self._frequency_cap.max_messages_per_day}",
                messages_sent_today=messages_today,
                messages_sent_this_week=messages_this_week,
                messages_sent_this_month=messages_this_month,
            )

        # Check weekly cap
        if messages_this_week >= self._frequency_cap.max_messages_per_week:
            return FrequencyCheckResult(
                allowed=False,
                reason=f"Weekly cap reached: {messages_this_week}/{self._frequency_cap.max_messages_per_week}",
                messages_sent_today=messages_today,
                messages_sent_this_week=messages_this_week,
                messages_sent_this_month=messages_this_month,
            )

        # Check monthly cap
        if messages_this_month >= self._frequency_cap.max_messages_per_month:
            return FrequencyCheckResult(
                allowed=False,
                reason=f"Monthly cap reached: {messages_this_month}/{self._frequency_cap.max_messages_per_month}",
                messages_sent_today=messages_today,
                messages_sent_this_week=messages_this_week,
                messages_sent_this_month=messages_this_month,
            )

        # Check channel-specific caps
        if message.campaign_type == CampaignType.EMAIL:
            emails_this_week = sum(
                1 for attempt in self._state.message_history
                if attempt.timestamp >= week_ago
                and attempt.campaign_type == CampaignType.EMAIL
                and attempt.success
            )
            if emails_this_week >= self._frequency_cap.max_emails_per_week:
                return FrequencyCheckResult(
                    allowed=False,
                    reason=f"Email weekly cap reached: {emails_this_week}/{self._frequency_cap.max_emails_per_week}",
                    messages_sent_today=messages_today,
                    messages_sent_this_week=messages_this_week,
                    messages_sent_this_month=messages_this_month,
                )

        elif message.campaign_type == CampaignType.SMS:
            sms_this_week = sum(
                1 for attempt in self._state.message_history
                if attempt.timestamp >= week_ago
                and attempt.campaign_type == CampaignType.SMS
                and attempt.success
            )
            if sms_this_week >= self._frequency_cap.max_sms_per_week:
                return FrequencyCheckResult(
                    allowed=False,
                    reason=f"SMS weekly cap reached: {sms_this_week}/{self._frequency_cap.max_sms_per_week}",
                    messages_sent_today=messages_today,
                    messages_sent_this_week=messages_this_week,
                    messages_sent_this_month=messages_this_month,
                )

        # Check minimum time between messages
        if self._state.last_message_time:
            hours_since_last = (now - self._state.last_message_time).total_seconds() / 3600
            if hours_since_last < self._frequency_cap.min_hours_between_messages:
                return FrequencyCheckResult(
                    allowed=False,
                    reason=f"Minimum time between messages not met: "
                          f"{hours_since_last:.1f}h < {self._frequency_cap.min_hours_between_messages}h",
                    messages_sent_today=messages_today,
                    messages_sent_this_week=messages_this_week,
                    messages_sent_this_month=messages_this_month,
                    hours_since_last_message=hours_since_last,
                )
        else:
            hours_since_last = None

        # All checks passed!
        return FrequencyCheckResult(
            allowed=True,
            reason="All frequency checks passed",
            messages_sent_today=messages_today,
            messages_sent_this_week=messages_this_week,
            messages_sent_this_month=messages_this_month,
            hours_since_last_message=hours_since_last,
        )

    @workflow.query
    def is_opted_out(self, channel: CampaignType) -> bool:
        """Query: Check if user opted out of a channel."""
        return channel in self._state.opted_out_channels

    # SIGNALS - Update user state (called by campaign workflows)

    @workflow.signal
    def record_message_sent(self, message: CampaignMessage, success: bool) -> None:
        """
        Signal: Record that a message was sent.

        Campaign workflows call this AFTER sending a message.
        """
        now = workflow.now()

        attempt = MessageAttempt(
            timestamp=now,
            campaign_id=message.campaign_id,
            campaign_name=message.campaign_name,
            campaign_type=message.campaign_type,
            success=success,
            reason=None if success else "Send failed"
        )

        self._state.message_history.append(attempt)

        if success:
            self._state.total_messages_sent += 1
            self._state.last_message_time = now

        workflow.logger.info(
            f"📝 Recorded message: {message.campaign_name} "
            f"({'success' if success else 'failed'}) - "
            f"Total sent: {self._state.total_messages_sent}"
        )

        # Keep only last 1000 messages to prevent unbounded growth
        if len(self._state.message_history) > 1000:
            self._state.message_history = self._state.message_history[-1000:]

    @workflow.signal
    def opt_out_channel(self, channel: CampaignType) -> None:
        """Signal: User opts out of a channel."""
        if channel not in self._state.opted_out_channels:
            self._state.opted_out_channels.append(channel)
            workflow.logger.info(f"🚫 User {self._user_id} opted out of {channel.value}")

    @workflow.signal
    def opt_in_channel(self, channel: CampaignType) -> None:
        """Signal: User opts back in to a channel."""
        if channel in self._state.opted_out_channels:
            self._state.opted_out_channels.remove(channel)
            workflow.logger.info(f"✅ User {self._user_id} opted in to {channel.value}")

    @workflow.signal
    def update_preferences(self, preferences: dict) -> None:
        """Signal: Update user preferences."""
        self._state.preferences.update(preferences)
        workflow.logger.info(f"⚙️ Updated preferences for {self._user_id}: {preferences}")

    @workflow.signal
    def update_frequency_cap(self, frequency_cap: FrequencyCap) -> None:
        """Signal: Update frequency cap settings."""
        self._frequency_cap = frequency_cap
        workflow.logger.info(f"📊 Updated frequency cap for {self._user_id}")
