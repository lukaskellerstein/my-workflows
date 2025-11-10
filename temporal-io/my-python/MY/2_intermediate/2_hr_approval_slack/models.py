"""Data models for HR approval workflow."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class RequestType(str, Enum):
    """Types of HR requests."""
    TIME_OFF = "time_off"
    EXPENSE_REIMBURSEMENT = "expense_reimbursement"
    EQUIPMENT_REQUEST = "equipment_request"
    PROMOTION = "promotion"
    TRANSFER = "transfer"


class ApprovalStatus(str, Enum):
    """Approval status states."""
    PENDING = "pending"
    MANAGER_APPROVED = "manager_approved"
    HR_APPROVED = "hr_approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Request priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ApprovalRequest:
    """HR approval request details."""
    request_id: str
    employee_id: str
    employee_name: str
    request_type: RequestType
    title: str
    description: str
    priority: Priority
    amount: Optional[float] = None  # For expense reimbursements
    start_date: Optional[datetime] = None  # For time off
    end_date: Optional[datetime] = None  # For time off


@dataclass
class ApprovalDecision:
    """Approval decision details."""
    approver_id: str
    approver_name: str
    approved: bool
    comments: str
    timestamp: datetime


@dataclass
class ApprovalState:
    """Complete approval request state."""
    request_id: str
    employee_id: str
    employee_name: str
    request_type: RequestType
    title: str
    description: str
    priority: Priority
    status: ApprovalStatus
    manager_decision: Optional[ApprovalDecision]
    hr_decision: Optional[ApprovalDecision]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    cancellation_reason: Optional[str]
