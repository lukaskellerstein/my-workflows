"""Data models for e-commerce order processing."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class OrderStatus(str, Enum):
    """Order status states."""
    PENDING = "pending"
    PAYMENT_CONFIRMED = "payment_confirmed"
    PREPARING = "preparing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class ShippingProvider(str, Enum):
    """Shipping provider options."""
    FEDEX = "fedex"
    UPS = "ups"
    DHL = "dhl"


@dataclass
class OrderItem:
    """Individual order item."""
    product_id: str
    product_name: str
    quantity: int
    price: float


@dataclass
class ShippingInfo:
    """Shipping information."""
    address: str
    city: str
    postal_code: str
    country: str


@dataclass
class OrderDetails:
    """Order details."""
    order_id: str
    customer_id: str
    items: list[OrderItem]
    total_amount: float
    shipping_info: ShippingInfo


@dataclass
class PaymentInfo:
    """Payment confirmation information."""
    transaction_id: str
    amount: float
    payment_method: str
    timestamp: datetime


@dataclass
class ShipmentInfo:
    """Shipment tracking information."""
    tracking_number: str
    provider: ShippingProvider
    estimated_delivery: datetime
    shipped_at: datetime


@dataclass
class OrderState:
    """Complete order state for queries."""
    order_id: str
    customer_id: str
    status: OrderStatus
    total_amount: float
    payment_info: Optional[PaymentInfo]
    shipment_info: Optional[ShipmentInfo]
    created_at: datetime
    updated_at: datetime
    estimated_delivery: Optional[datetime]
    cancellation_reason: Optional[str]
