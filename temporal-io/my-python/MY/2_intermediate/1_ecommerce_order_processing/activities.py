"""Activities for order processing."""

import asyncio
from datetime import datetime, timedelta
from temporalio import activity

from models import OrderDetails, PaymentInfo, ShipmentInfo, ShippingProvider


@activity.defn
async def reserve_inventory(order_details: OrderDetails) -> bool:
    """Reserve inventory for the order."""
    activity.logger.info(f"Reserving inventory for order {order_details.order_id}")

    # Simulate inventory reservation
    await asyncio.sleep(1)

    # Check if all items are available
    for item in order_details.items:
        activity.logger.info(
            f"Reserved {item.quantity}x {item.product_name} (ID: {item.product_id})"
        )

    return True


@activity.defn
async def process_payment(order_details: OrderDetails, payment_info: PaymentInfo) -> bool:
    """Process the payment."""
    activity.logger.info(
        f"Processing payment for order {order_details.order_id}: "
        f"${payment_info.amount} via {payment_info.payment_method}"
    )

    # Simulate payment processing
    await asyncio.sleep(2)

    activity.logger.info(
        f"Payment successful. Transaction ID: {payment_info.transaction_id}"
    )

    return True


@activity.defn
async def prepare_shipment(order_details: OrderDetails) -> str:
    """Prepare the order for shipment."""
    activity.logger.info(f"Preparing shipment for order {order_details.order_id}")

    # Simulate shipment preparation
    await asyncio.sleep(2)

    activity.logger.info(f"Order {order_details.order_id} packaged and ready")

    return f"PKG-{order_details.order_id}"


@activity.defn
async def ship_order(
    order_details: OrderDetails,
    package_id: str,
    provider: ShippingProvider
) -> ShipmentInfo:
    """Ship the order."""
    activity.logger.info(
        f"Shipping order {order_details.order_id} via {provider.value}"
    )

    # Simulate shipping
    await asyncio.sleep(1)

    tracking_number = f"{provider.value.upper()}-{order_details.order_id}-{package_id}"

    shipment_info = ShipmentInfo(
        tracking_number=tracking_number,
        provider=provider,
        estimated_delivery=datetime.now() + timedelta(days=3),
        shipped_at=datetime.now()
    )

    activity.logger.info(
        f"Order shipped! Tracking: {tracking_number}, "
        f"ETA: {shipment_info.estimated_delivery}"
    )

    return shipment_info


@activity.defn
async def send_email_notification(
    customer_id: str,
    order_id: str,
    subject: str,
    message: str
) -> None:
    """Send email notification to customer."""
    activity.logger.info(
        f"Sending email to customer {customer_id} about order {order_id}"
    )
    activity.logger.info(f"Subject: {subject}")
    activity.logger.info(f"Message: {message}")

    # Simulate email sending
    await asyncio.sleep(0.5)


@activity.defn
async def release_inventory(order_details: OrderDetails) -> None:
    """Release reserved inventory (compensation)."""
    activity.logger.info(
        f"Releasing inventory for cancelled order {order_details.order_id}"
    )

    for item in order_details.items:
        activity.logger.info(
            f"Released {item.quantity}x {item.product_name}"
        )

    await asyncio.sleep(1)


@activity.defn
async def refund_payment(payment_info: PaymentInfo) -> None:
    """Refund payment (compensation)."""
    activity.logger.info(
        f"Processing refund for transaction {payment_info.transaction_id}: "
        f"${payment_info.amount}"
    )

    await asyncio.sleep(2)

    activity.logger.info("Refund processed successfully")
