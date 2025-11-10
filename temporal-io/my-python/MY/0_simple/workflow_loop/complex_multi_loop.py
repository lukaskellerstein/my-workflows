"""
Example: Complex Workflow with MULTIPLE LOOPS (including nested loops)

Use Case: E-Commerce Order Fulfillment System
This demonstrates a realistic, complex workflow with:
- 3 main loops
- Nested loops within loops
- Multiple decision points

Workflow Structure:
1. ORDER VALIDATION LOOP - Validate customer, inventory, payment
2. FULFILLMENT LOOP (with nested PACKAGING LOOP)
3. DELIVERY LOOP - Attempt delivery with retry logic

This represents a real-world scenario where multiple stages can fail
and need to loop back for corrections.
"""
import asyncio
import random
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import timedelta
from typing import List, Optional

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Customer:
    id: str
    name: str
    credit_score: int
    is_verified: bool = False


@dataclass
class OrderItem:
    sku: str
    name: str
    quantity: int
    price: float


@dataclass
class Order:
    order_id: str
    customer: Customer
    items: List[OrderItem]
    total_amount: float
    payment_verified: bool = False
    inventory_reserved: bool = False
    validation_attempts: int = 0


@dataclass
class PackageBox:
    box_id: str
    items: List[OrderItem]
    weight: float
    is_sealed: bool = False
    quality_passed: bool = False


@dataclass
class Shipment:
    tracking_number: str
    packages: List[PackageBox]
    address: str
    carrier: str
    attempts: int = 0


@dataclass
class ValidationResult:
    passed: bool
    issues: List[str] = field(default_factory=list)
    retry_possible: bool = True


@dataclass
class DeliveryAttemptResult:
    delivered: bool
    reason: Optional[str] = None
    retry_recommended: bool = False


# ============================================================================
# LOOP 1: ORDER VALIDATION ACTIVITIES
# ============================================================================

@activity.defn
def verify_customer(customer: Customer, attempt: int) -> ValidationResult:
    activity.logger.info(f"[1.1 VERIFY CUSTOMER] Attempt {attempt} - Customer: {customer.name}")

    # Simulate: customers with credit score < 600 need manual verification
    if customer.credit_score < 600 and not customer.is_verified:
        activity.logger.warning(f"[1.1] Customer {customer.name} needs manual verification")
        # Simulate that verification happens after first attempt
        if attempt > 1:
            customer.is_verified = True
            activity.logger.info(f"[1.1] Customer verified on attempt {attempt}")
            return ValidationResult(passed=True, issues=[])
        return ValidationResult(
            passed=False,
            issues=["Customer needs manual verification"],
            retry_possible=True
        )

    activity.logger.info(f"[1.1] Customer {customer.name} verified")
    return ValidationResult(passed=True, issues=[])


@activity.defn
def check_inventory(items: List[OrderItem], attempt: int) -> ValidationResult:
    activity.logger.info(f"[1.2 CHECK INVENTORY] Attempt {attempt} - Checking {len(items)} items")

    # Simulate: 40% chance of stock issues on first attempt, resolved on retry
    if attempt == 1 and random.random() < 0.4:
        activity.logger.warning(f"[1.2] Inventory shortage detected")
        return ValidationResult(
            passed=False,
            issues=["Inventory needs replenishment"],
            retry_possible=True
        )

    activity.logger.info(f"[1.2] All items in stock")
    return ValidationResult(passed=True, issues=[])


@activity.defn
def verify_payment(amount: float, customer: Customer, attempt: int) -> ValidationResult:
    activity.logger.info(f"[1.3 VERIFY PAYMENT] Attempt {attempt} - Amount: ${amount}")

    # Simulate: payment verification issues resolved after retry
    if attempt == 1 and random.random() < 0.3:
        activity.logger.warning(f"[1.3] Payment verification pending")
        return ValidationResult(
            passed=False,
            issues=["Payment authorization pending"],
            retry_possible=True
        )

    activity.logger.info(f"[1.3] Payment verified: ${amount}")
    return ValidationResult(passed=True, issues=[])


@activity.defn
def reserve_inventory(items: List[OrderItem]) -> bool:
    activity.logger.info(f"[1.4 RESERVE INVENTORY] Reserving {len(items)} items")
    # Simulate reservation
    return True


# ============================================================================
# LOOP 2: FULFILLMENT ACTIVITIES (with nested packaging loop)
# ============================================================================

@activity.defn
def pick_items(items: List[OrderItem], attempt: int) -> ValidationResult:
    activity.logger.info(f"[2.1 PICK ITEMS] Attempt {attempt} - Picking {len(items)} items")

    # Simulate: 20% chance of picking error
    if attempt == 1 and random.random() < 0.2:
        activity.logger.warning(f"[2.1] Item picking error - wrong item selected")
        return ValidationResult(
            passed=False,
            issues=["Wrong item picked, need to re-pick"],
            retry_possible=True
        )

    activity.logger.info(f"[2.1] All items picked successfully")
    return ValidationResult(passed=True, issues=[])


# NESTED LOOP 2A: PACKAGING SUB-LOOP

@activity.defn
def pack_items_in_box(items: List[OrderItem], box_attempt: int) -> PackageBox:
    activity.logger.info(f"[2.2.1 PACK ITEMS] Box attempt {box_attempt}")

    total_weight = sum(item.quantity * 0.5 for item in items)  # Simulate weight
    box = PackageBox(
        box_id=f"BOX-{box_attempt}",
        items=items,
        weight=total_weight,
        is_sealed=False,
        quality_passed=False
    )

    activity.logger.info(f"[2.2.1] Items packed in box {box.box_id}, weight: {box.weight}kg")
    return box


@activity.defn
def seal_package(package: PackageBox) -> PackageBox:
    activity.logger.info(f"[2.2.2 SEAL PACKAGE] Sealing box {package.box_id}")
    package.is_sealed = True
    return package


@activity.defn
def quality_check_package(package: PackageBox, check_attempt: int) -> ValidationResult:
    activity.logger.info(f"[2.2.3 QUALITY CHECK] Box {package.box_id}, attempt {check_attempt}")

    # Simulate: 30% failure rate on first check, passes on retry
    if check_attempt == 1 and random.random() < 0.3:
        activity.logger.warning(f"[2.2.3] Quality check FAILED - package damaged or incorrect")
        return ValidationResult(
            passed=False,
            issues=["Package quality issue - needs repackaging"],
            retry_possible=True
        )

    activity.logger.info(f"[2.2.3] Quality check PASSED")
    package.quality_passed = True
    return ValidationResult(passed=True, issues=[])


@activity.defn
def print_shipping_label(order_id: str, package: PackageBox) -> str:
    activity.logger.info(f"[2.3 PRINT LABEL] Order {order_id}, Box {package.box_id}")
    tracking = f"TRACK-{order_id}-{package.box_id}"
    activity.logger.info(f"[2.3] Label printed: {tracking}")
    return tracking


# ============================================================================
# LOOP 3: DELIVERY ACTIVITIES
# ============================================================================

@activity.defn
def assign_carrier(shipment: Shipment) -> str:
    activity.logger.info(f"[3.1 ASSIGN CARRIER] Tracking: {shipment.tracking_number}")
    carriers = ["FastShip", "QuickDeliver", "ExpressGo"]
    carrier = random.choice(carriers)
    activity.logger.info(f"[3.1] Assigned carrier: {carrier}")
    return carrier


@activity.defn
def attempt_delivery(shipment: Shipment, attempt: int) -> DeliveryAttemptResult:
    activity.logger.info(
        f"[3.2 ATTEMPT DELIVERY] Attempt {attempt}/{3} - Tracking: {shipment.tracking_number}"
    )

    # Simulate delivery success rate: 40% attempt 1, 70% attempt 2, 100% attempt 3
    success_rates = {1: 0.4, 2: 0.7, 3: 1.0}
    success_rate = success_rates.get(attempt, 1.0)

    if random.random() < success_rate:
        activity.logger.info(f"[3.2] ✓ Delivery SUCCESSFUL on attempt {attempt}")
        return DeliveryAttemptResult(delivered=True, reason="Package delivered")
    else:
        reasons = ["Customer not home", "Address access issue", "Weather delay"]
        reason = random.choice(reasons)
        activity.logger.warning(f"[3.2] ✗ Delivery FAILED: {reason}")
        return DeliveryAttemptResult(
            delivered=False,
            reason=reason,
            retry_recommended=attempt < 3
        )


@activity.defn
def notify_customer_delivery_failed(shipment: Shipment, reason: str, attempt: int) -> None:
    activity.logger.info(
        f"[3.3 NOTIFY CUSTOMER] Delivery attempt {attempt} failed: {reason}"
    )


@activity.defn
def confirm_delivery(tracking_number: str) -> str:
    activity.logger.info(f"[3.4 CONFIRM DELIVERY] Tracking: {tracking_number}")
    return f"Delivery confirmed for {tracking_number}"


@activity.defn
def process_delivery_failure(shipment: Shipment) -> str:
    activity.logger.error(
        f"[3.5 DELIVERY FAILURE] Failed to deliver after max attempts: {shipment.tracking_number}"
    )
    return f"Delivery failed - initiating return process for {shipment.tracking_number}"


# ============================================================================
# MAIN WORKFLOW WITH MULTIPLE LOOPS
# ============================================================================

@workflow.defn
class ComplexMultiLoopWorkflow:
    @workflow.run
    async def run(self, order: Order, delivery_address: str) -> str:
        workflow.logger.info("="*70)
        workflow.logger.info(f"STARTING COMPLEX ORDER FULFILLMENT WORKFLOW")
        workflow.logger.info(f"Order ID: {order.order_id}")
        workflow.logger.info(f"Customer: {order.customer.name}")
        workflow.logger.info(f"Items: {len(order.items)}")
        workflow.logger.info(f"Total: ${order.total_amount}")
        workflow.logger.info("="*70)

        # ====================================================================
        # LOOP 1: ORDER VALIDATION LOOP
        # ====================================================================
        workflow.logger.info("\n" + "▼"*35)
        workflow.logger.info("PHASE 1: ORDER VALIDATION (LOOP 1)")
        workflow.logger.info("▼"*35)

        max_validation_attempts = 3
        validation_passed = False

        while order.validation_attempts < max_validation_attempts and not validation_passed:
            order.validation_attempts += 1
            workflow.logger.info(f"\n┌─ VALIDATION LOOP - Attempt {order.validation_attempts} ─┐")

            # Step 1.1: Verify customer
            workflow.logger.info("│ Step 1.1: Verifying customer...")
            customer_result = await workflow.execute_activity(
                verify_customer,
                args=[order.customer, order.validation_attempts],
                start_to_close_timeout=timedelta(seconds=10),
            )

            if not customer_result.passed:
                workflow.logger.warning(f"│ ✗ Customer verification failed: {customer_result.issues}")
                workflow.logger.info(f"│ ↻ LOOP BACK - Retrying validation...")
                await asyncio.sleep(1)  # Simulate waiting for manual verification
                continue

            # Step 1.2: Check inventory
            workflow.logger.info("│ Step 1.2: Checking inventory...")
            inventory_result = await workflow.execute_activity(
                check_inventory,
                args=[order.items, order.validation_attempts],
                start_to_close_timeout=timedelta(seconds=10),
            )

            if not inventory_result.passed:
                workflow.logger.warning(f"│ ✗ Inventory check failed: {inventory_result.issues}")
                workflow.logger.info(f"│ ↻ LOOP BACK - Retrying validation...")
                await asyncio.sleep(1)  # Simulate waiting for restock
                continue

            # Step 1.3: Verify payment
            workflow.logger.info("│ Step 1.3: Verifying payment...")
            payment_result = await workflow.execute_activity(
                verify_payment,
                args=[order.total_amount, order.customer, order.validation_attempts],
                start_to_close_timeout=timedelta(seconds=10),
            )

            if not payment_result.passed:
                workflow.logger.warning(f"│ ✗ Payment verification failed: {payment_result.issues}")
                workflow.logger.info(f"│ ↻ LOOP BACK - Retrying validation...")
                await asyncio.sleep(1)  # Simulate waiting for payment auth
                continue

            # All validations passed
            validation_passed = True
            workflow.logger.info("│ ✓ All validations PASSED!")
            workflow.logger.info("└" + "─"*40 + "┘")

        if not validation_passed:
            return f"Order validation FAILED after {max_validation_attempts} attempts"

        # Step 1.4: Reserve inventory
        workflow.logger.info("\nStep 1.4: Reserving inventory...")
        order.inventory_reserved = await workflow.execute_activity(
            reserve_inventory,
            order.items,
            start_to_close_timeout=timedelta(seconds=10),
        )

        workflow.logger.info(f"✓ PHASE 1 COMPLETE - Order validated in {order.validation_attempts} attempt(s)")

        # ====================================================================
        # LOOP 2: FULFILLMENT LOOP (with nested packaging loop)
        # ====================================================================
        workflow.logger.info("\n" + "▼"*35)
        workflow.logger.info("PHASE 2: FULFILLMENT (LOOP 2 with nested LOOP 2A)")
        workflow.logger.info("▼"*35)

        max_fulfillment_attempts = 3
        fulfillment_attempt = 0
        fulfillment_complete = False
        final_package = None

        while fulfillment_attempt < max_fulfillment_attempts and not fulfillment_complete:
            fulfillment_attempt += 1
            workflow.logger.info(f"\n┌─ FULFILLMENT LOOP - Attempt {fulfillment_attempt} ─┐")

            # Step 2.1: Pick items
            workflow.logger.info("│ Step 2.1: Picking items from warehouse...")
            pick_result = await workflow.execute_activity(
                pick_items,
                args=[order.items, fulfillment_attempt],
                start_to_close_timeout=timedelta(seconds=10),
            )

            if not pick_result.passed:
                workflow.logger.warning(f"│ ✗ Item picking failed: {pick_result.issues}")
                workflow.logger.info(f"│ ↻ LOOP BACK - Retrying fulfillment...")
                continue

            # ================================================================
            # NESTED LOOP 2A: PACKAGING QUALITY LOOP
            # ================================================================
            workflow.logger.info("│")
            workflow.logger.info("│ ┌─ NESTED PACKAGING LOOP (LOOP 2A) ─┐")

            max_packaging_attempts = 3
            packaging_attempt = 0
            packaging_complete = False
            current_package = None

            while packaging_attempt < max_packaging_attempts and not packaging_complete:
                packaging_attempt += 1
                workflow.logger.info(f"│ │ Packaging Attempt {packaging_attempt}")

                # Step 2.2.1: Pack items
                workflow.logger.info("│ │ Step 2.2.1: Packing items in box...")
                current_package = await workflow.execute_activity(
                    pack_items_in_box,
                    args=[order.items, packaging_attempt],
                    start_to_close_timeout=timedelta(seconds=10),
                )

                # Step 2.2.2: Seal package
                workflow.logger.info("│ │ Step 2.2.2: Sealing package...")
                current_package = await workflow.execute_activity(
                    seal_package,
                    current_package,
                    start_to_close_timeout=timedelta(seconds=10),
                )

                # Step 2.2.3: Quality check
                workflow.logger.info("│ │ Step 2.2.3: Quality checking package...")
                quality_result = await workflow.execute_activity(
                    quality_check_package,
                    args=[current_package, packaging_attempt],
                    start_to_close_timeout=timedelta(seconds=10),
                )

                if not quality_result.passed:
                    workflow.logger.warning(f"│ │ ✗ Quality check failed: {quality_result.issues}")
                    workflow.logger.info(f"│ │ ↻ NESTED LOOP BACK - Repackaging...")
                    continue

                # Packaging complete
                packaging_complete = True
                workflow.logger.info("│ │ ✓ Packaging quality check PASSED!")
                workflow.logger.info("│ └" + "─"*35 + "┘")

            if not packaging_complete:
                workflow.logger.error("│ ✗ Packaging failed after max attempts")
                workflow.logger.info("│ ↻ LOOP BACK - Retrying entire fulfillment...")
                continue

            final_package = current_package

            # Step 2.3: Print shipping label
            workflow.logger.info("│ Step 2.3: Printing shipping label...")
            tracking_number = await workflow.execute_activity(
                print_shipping_label,
                args=[order.order_id, final_package],
                start_to_close_timeout=timedelta(seconds=10),
            )

            fulfillment_complete = True
            workflow.logger.info("│ ✓ Fulfillment COMPLETE!")
            workflow.logger.info("└" + "─"*40 + "┘")

        if not fulfillment_complete:
            return f"Fulfillment FAILED after {max_fulfillment_attempts} attempts"

        workflow.logger.info(
            f"✓ PHASE 2 COMPLETE - Fulfillment done in {fulfillment_attempt} attempt(s)"
        )

        # ====================================================================
        # LOOP 3: DELIVERY LOOP
        # ====================================================================
        workflow.logger.info("\n" + "▼"*35)
        workflow.logger.info("PHASE 3: DELIVERY (LOOP 3)")
        workflow.logger.info("▼"*35)

        # Create shipment
        shipment = Shipment(
            tracking_number=tracking_number,
            packages=[final_package],
            address=delivery_address,
            carrier="",
            attempts=0
        )

        # Step 3.1: Assign carrier
        workflow.logger.info("\nStep 3.1: Assigning carrier...")
        shipment.carrier = await workflow.execute_activity(
            assign_carrier,
            shipment,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Delivery attempt loop
        max_delivery_attempts = 3
        delivered = False

        while shipment.attempts < max_delivery_attempts and not delivered:
            shipment.attempts += 1
            workflow.logger.info(f"\n┌─ DELIVERY LOOP - Attempt {shipment.attempts} ─┐")

            # Step 3.2: Attempt delivery
            workflow.logger.info(f"│ Step 3.2: Attempting delivery (attempt {shipment.attempts})...")
            delivery_result = await workflow.execute_activity(
                attempt_delivery,
                args=[shipment, shipment.attempts],
                start_to_close_timeout=timedelta(seconds=10),
            )

            if delivery_result.delivered:
                delivered = True
                workflow.logger.info("│ ✓ Package DELIVERED successfully!")
                workflow.logger.info("└" + "─"*40 + "┘")
            else:
                workflow.logger.warning(f"│ ✗ Delivery failed: {delivery_result.reason}")

                # Step 3.3: Notify customer
                workflow.logger.info("│ Step 3.3: Notifying customer of failed attempt...")
                await workflow.execute_activity(
                    notify_customer_delivery_failed,
                    args=[shipment, delivery_result.reason, shipment.attempts],
                    start_to_close_timeout=timedelta(seconds=10),
                )

                if delivery_result.retry_recommended and shipment.attempts < max_delivery_attempts:
                    workflow.logger.info(f"│ ↻ LOOP BACK - Retrying delivery...")
                    workflow.logger.info("└" + "─"*40 + "┘")
                    await asyncio.sleep(1)  # Simulate waiting before retry
                else:
                    workflow.logger.info("└" + "─"*40 + "┘")

        # Final delivery outcome
        if delivered:
            # Step 3.4: Confirm delivery
            workflow.logger.info("\nStep 3.4: Confirming delivery...")
            confirmation = await workflow.execute_activity(
                confirm_delivery,
                tracking_number,
                start_to_close_timeout=timedelta(seconds=10),
            )

            workflow.logger.info(f"✓ PHASE 3 COMPLETE - Delivered in {shipment.attempts} attempt(s)")

            # Final summary
            workflow.logger.info("\n" + "="*70)
            workflow.logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
            workflow.logger.info("="*70)
            workflow.logger.info(f"Order ID: {order.order_id}")
            workflow.logger.info(f"Validation attempts: {order.validation_attempts}")
            workflow.logger.info(f"Fulfillment attempts: {fulfillment_attempt}")
            workflow.logger.info(f"Delivery attempts: {shipment.attempts}")
            workflow.logger.info(f"Tracking: {tracking_number}")
            workflow.logger.info("="*70)

            return (
                f"✓ Order {order.order_id} completed successfully!\n"
                f"Tracking: {tracking_number}\n"
                f"Total workflow attempts:\n"
                f"  - Validation: {order.validation_attempts}\n"
                f"  - Fulfillment: {fulfillment_attempt}\n"
                f"  - Delivery: {shipment.attempts}\n"
                f"{confirmation}"
            )
        else:
            # Step 3.5: Process delivery failure
            workflow.logger.error("\nStep 3.5: Processing delivery failure...")
            failure_result = await workflow.execute_activity(
                process_delivery_failure,
                shipment,
                start_to_close_timeout=timedelta(seconds=10),
            )

            workflow.logger.info("="*70)
            workflow.logger.info("WORKFLOW COMPLETED WITH DELIVERY FAILURE")
            workflow.logger.info("="*70)

            return (
                f"✗ Order {order.order_id} - Delivery failed after {max_delivery_attempts} attempts\n"
                f"{failure_result}"
            )


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue="complex-multi-loop-task-queue",
        workflows=[ComplexMultiLoopWorkflow],
        activities=[
            # Loop 1 activities
            verify_customer,
            check_inventory,
            verify_payment,
            reserve_inventory,
            # Loop 2 activities
            pick_items,
            pack_items_in_box,
            seal_package,
            quality_check_package,
            print_shipping_label,
            # Loop 3 activities
            assign_carrier,
            attempt_delivery,
            notify_customer_delivery_failed,
            confirm_delivery,
            process_delivery_failure,
        ],
        activity_executor=ThreadPoolExecutor(10),
    ):
        # Create test order
        customer = Customer(
            id="CUST-001",
            name="John Doe",
            credit_score=550,  # Low score - will trigger customer verification loop
            is_verified=False
        )

        items = [
            OrderItem(sku="WIDGET-A", name="Premium Widget", quantity=2, price=50.0),
            OrderItem(sku="GADGET-B", name="Smart Gadget", quantity=1, price=150.0),
            OrderItem(sku="TOOL-C", name="Professional Tool", quantity=3, price=30.0),
        ]

        order = Order(
            order_id="ORD-2024-001",
            customer=customer,
            items=items,
            total_amount=340.0,
            payment_verified=False,
            inventory_reserved=False,
            validation_attempts=0
        )

        delivery_address = "123 Main St, Anytown, ST 12345"

        print("\n" + "="*70)
        print("EXECUTING: Complex Multi-Loop Workflow")
        print("="*70)
        print("\nThis workflow demonstrates:")
        print("  • LOOP 1: Order Validation (customer, inventory, payment)")
        print("  • LOOP 2: Fulfillment with NESTED LOOP 2A (packaging quality)")
        print("  • LOOP 3: Delivery attempts")
        print("\nExpected behavior:")
        print("  - Customer verification may loop 1-2 times (low credit score)")
        print("  - Inventory/payment may loop once")
        print("  - Packaging quality may loop 1-2 times")
        print("  - Delivery will attempt up to 3 times")
        print("="*70 + "\n")

        # Execute the workflow
        result = await client.execute_workflow(
            ComplexMultiLoopWorkflow.run,
            args=[order, delivery_address],
            id="complex-multi-loop-workflow",
            task_queue="complex-multi-loop-task-queue",
        )

        print("\n" + "="*70)
        print("FINAL WORKFLOW RESULT:")
        print("="*70)
        print(result)
        print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
