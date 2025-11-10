"""Order processing workflow with Signals and Queries."""

from datetime import datetime, timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from models import (
        OrderDetails,
        OrderState,
        OrderStatus,
        PaymentInfo,
        ShipmentInfo,
        ShippingProvider,
    )
    from activities import (
        reserve_inventory,
        process_payment,
        prepare_shipment,
        ship_order,
        send_email_notification,
        release_inventory,
        refund_payment,
    )


@workflow.defn
class OrderProcessingWorkflow:
    """
    E-commerce order processing workflow demonstrating Signals and Queries.

    Signals:
    - confirm_payment: External payment gateway confirms payment
    - ship_order_signal: Warehouse confirms shipment
    - cancel_order: Customer or admin cancels the order

    Queries:
    - get_order_status: Get current order status
    - get_full_state: Get complete order state
    - get_estimated_delivery: Get estimated delivery date
    """

    def __init__(self) -> None:
        """Initialize workflow state."""
        self._order_details: OrderDetails | None = None
        self._status = OrderStatus.PENDING
        self._payment_info: PaymentInfo | None = None
        self._shipment_info: ShipmentInfo | None = None
        self._created_at: datetime | None = None
        self._updated_at: datetime | None = None
        self._cancellation_reason: str | None = None

        # Control flags
        self._payment_confirmed = False
        self._should_cancel = False
        self._inventory_reserved = False

    @workflow.run
    async def run(self, order_details: OrderDetails) -> OrderState:
        """Main workflow execution."""
        self._order_details = order_details
        self._created_at = workflow.now()
        self._updated_at = workflow.now()

        workflow.logger.info(f"Starting order processing for {order_details.order_id}")

        try:
            # Step 1: Reserve inventory
            workflow.logger.info("Step 1: Reserving inventory...")
            self._inventory_reserved = await workflow.execute_activity(
                reserve_inventory,
                order_details,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            # Send confirmation email
            await workflow.execute_activity(
                send_email_notification,
                args=[
                    order_details.customer_id,
                    order_details.order_id,
                    "Order Received",
                    f"Your order {order_details.order_id} has been received. "
                    f"Awaiting payment confirmation."
                ],
                start_to_close_timeout=timedelta(seconds=10),
            )

            # Step 2: Wait for payment confirmation (SIGNAL)
            workflow.logger.info("Step 2: Waiting for payment confirmation...")
            await workflow.wait_condition(
                lambda: self._payment_confirmed or self._should_cancel,
                timeout=timedelta(hours=24)
            )

            if self._should_cancel:
                return await self._handle_cancellation()

            # Step 3: Process payment
            workflow.logger.info("Step 3: Processing payment...")
            self._status = OrderStatus.PAYMENT_CONFIRMED
            self._updated_at = workflow.now()

            await workflow.execute_activity(
                process_payment,
                args=[order_details, self._payment_info],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            # Send payment confirmation
            await workflow.execute_activity(
                send_email_notification,
                args=[
                    order_details.customer_id,
                    order_details.order_id,
                    "Payment Confirmed",
                    f"Payment of ${self._payment_info.amount} confirmed. "
                    f"Your order is being prepared for shipment."
                ],
                start_to_close_timeout=timedelta(seconds=10),
            )

            # Step 4: Prepare shipment
            workflow.logger.info("Step 4: Preparing shipment...")
            self._status = OrderStatus.PREPARING
            self._updated_at = workflow.now()

            package_id = await workflow.execute_activity(
                prepare_shipment,
                order_details,
                start_to_close_timeout=timedelta(minutes=5),
            )

            # Step 5: Ship the order
            workflow.logger.info("Step 5: Shipping order...")
            self._shipment_info = await workflow.execute_activity(
                ship_order,
                args=[order_details, package_id, ShippingProvider.FEDEX],
                start_to_close_timeout=timedelta(seconds=30),
            )

            self._status = OrderStatus.SHIPPED
            self._updated_at = workflow.now()

            # Send shipment notification
            await workflow.execute_activity(
                send_email_notification,
                args=[
                    order_details.customer_id,
                    order_details.order_id,
                    "Order Shipped",
                    f"Your order has been shipped! "
                    f"Tracking: {self._shipment_info.tracking_number}. "
                    f"Estimated delivery: {self._shipment_info.estimated_delivery}"
                ],
                start_to_close_timeout=timedelta(seconds=10),
            )

            # Step 6: Wait for delivery (simulated)
            workflow.logger.info("Step 6: Tracking delivery...")
            await workflow.sleep(timedelta(seconds=30))  # Simulate delivery time

            self._status = OrderStatus.DELIVERED
            self._updated_at = workflow.now()

            # Send delivery confirmation
            await workflow.execute_activity(
                send_email_notification,
                args=[
                    order_details.customer_id,
                    order_details.order_id,
                    "Order Delivered",
                    f"Your order {order_details.order_id} has been delivered. "
                    f"Thank you for shopping with us!"
                ],
                start_to_close_timeout=timedelta(seconds=10),
            )

            workflow.logger.info(f"Order {order_details.order_id} completed successfully")

            return self._get_current_state()

        except Exception as e:
            workflow.logger.error(f"Order processing failed: {e}")
            self._status = OrderStatus.CANCELLED
            self._cancellation_reason = f"System error: {str(e)}"
            self._updated_at = workflow.now()
            raise

    async def _handle_cancellation(self) -> OrderState:
        """Handle order cancellation with compensation."""
        workflow.logger.info(
            f"Cancelling order {self._order_details.order_id}: "
            f"{self._cancellation_reason}"
        )

        # Compensation logic
        if self._payment_info:
            workflow.logger.info("Refunding payment...")
            await workflow.execute_activity(
                refund_payment,
                self._payment_info,
                start_to_close_timeout=timedelta(seconds=30),
            )

        if self._inventory_reserved:
            workflow.logger.info("Releasing inventory...")
            await workflow.execute_activity(
                release_inventory,
                self._order_details,
                start_to_close_timeout=timedelta(seconds=30),
            )

        # Send cancellation email
        await workflow.execute_activity(
            send_email_notification,
            args=[
                self._order_details.customer_id,
                self._order_details.order_id,
                "Order Cancelled",
                f"Your order {self._order_details.order_id} has been cancelled. "
                f"Reason: {self._cancellation_reason}"
            ],
            start_to_close_timeout=timedelta(seconds=10),
        )

        self._status = OrderStatus.CANCELLED
        self._updated_at = workflow.now()

        return self._get_current_state()

    # SIGNALS - Receive data from external systems

    @workflow.signal
    def confirm_payment(self, payment_info: PaymentInfo) -> None:
        """Signal: Payment gateway confirms payment."""
        workflow.logger.info(
            f"Payment confirmed: ${payment_info.amount}, "
            f"Transaction: {payment_info.transaction_id}"
        )
        self._payment_info = payment_info
        self._payment_confirmed = True
        self._updated_at = workflow.now()

    @workflow.signal
    def cancel_order(self, reason: str) -> None:
        """Signal: Cancel the order."""
        workflow.logger.info(f"Order cancellation requested: {reason}")
        self._cancellation_reason = reason
        self._should_cancel = True
        self._updated_at = workflow.now()

    # QUERIES - Read current state without modification

    @workflow.query
    def get_order_status(self) -> str:
        """Query: Get current order status."""
        return self._status.value

    @workflow.query
    def get_full_state(self) -> OrderState:
        """Query: Get complete order state."""
        return self._get_current_state()

    @workflow.query
    def get_estimated_delivery(self) -> datetime | None:
        """Query: Get estimated delivery date."""
        if self._shipment_info:
            return self._shipment_info.estimated_delivery
        return None

    def _get_current_state(self) -> OrderState:
        """Build current order state."""
        return OrderState(
            order_id=self._order_details.order_id,
            customer_id=self._order_details.customer_id,
            status=self._status,
            total_amount=self._order_details.total_amount,
            payment_info=self._payment_info,
            shipment_info=self._shipment_info,
            created_at=self._created_at,
            updated_at=self._updated_at,
            estimated_delivery=self._shipment_info.estimated_delivery if self._shipment_info else None,
            cancellation_reason=self._cancellation_reason,
        )
