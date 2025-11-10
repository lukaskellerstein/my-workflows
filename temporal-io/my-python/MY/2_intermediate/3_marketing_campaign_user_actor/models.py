"""Data models for marketing campaign system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class CampaignType(str, Enum):
    """Types of marketing campaigns."""
    EMAIL = "email"
    SMS = "sms"
    PUSH_NOTIFICATION = "push_notification"
    IN_APP_MESSAGE = "in_app_message"


class CampaignPriority(str, Enum):
    """Campaign priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class CampaignMessage:
    """Individual campaign message."""
    campaign_id: str
    campaign_name: str
    campaign_type: CampaignType
    priority: CampaignPriority
    message_content: str
    metadata: dict = field(default_factory=dict)


@dataclass
class FrequencyCap:
    """Frequency capping rules."""
    max_messages_per_day: int = 3
    max_messages_per_week: int = 10
    max_messages_per_month: int = 30
    min_hours_between_messages: int = 2
    # Channel-specific caps
    max_emails_per_week: int = 5
    max_sms_per_week: int = 3


@dataclass
class MessageAttempt:
    """Record of a message send attempt."""
    timestamp: datetime
    campaign_id: str
    campaign_name: str
    campaign_type: CampaignType
    success: bool
    reason: Optional[str] = None


@dataclass
class UserState:
    """User actor state - shared across all campaigns."""
    user_id: str
    total_messages_sent: int = 0
    last_message_time: Optional[datetime] = None
    message_history: list[MessageAttempt] = field(default_factory=list)
    opted_out_channels: list[CampaignType] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)


@dataclass
class FrequencyCheckResult:
    """Result of frequency cap check."""
    allowed: bool
    reason: Optional[str] = None
    messages_sent_today: int = 0
    messages_sent_this_week: int = 0
    messages_sent_this_month: int = 0
    hours_since_last_message: Optional[float] = None
