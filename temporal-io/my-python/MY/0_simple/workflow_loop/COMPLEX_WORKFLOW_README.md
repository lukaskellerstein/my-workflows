# Complex Multi-Loop Workflow Example

## Overview

This example demonstrates a **realistic, production-grade workflow** with:
- **3 main loops** (Validation, Fulfillment, Delivery)
- **1 nested loop** (Packaging Quality inside Fulfillment)
- **15+ activities** organized across multiple phases
- **Multiple decision points** with conditional loop-back logic

## Use Case: E-Commerce Order Fulfillment

A complete order fulfillment system that handles:
1. Order validation (customer, inventory, payment)
2. Warehouse fulfillment with quality control
3. Delivery with retry logic

## Workflow Structure

### Phase 1: Order Validation Loop (LOOP 1)

**Purpose**: Ensure order can be fulfilled before starting expensive fulfillment operations

**Activities**:
- `1.1 verify_customer` - Validate customer creditworthiness
- `1.2 check_inventory` - Verify items are in stock
- `1.3 verify_payment` - Authorize payment
- `1.4 reserve_inventory` - Lock inventory for order

**Loop Behavior**:
- If **any** validation fails → Loop back to 1.1
- Each iteration may resolve different issues:
  - Customer verification (manual approval)
  - Inventory restocking
  - Payment authorization delay
- Max 3 attempts before failing order

**Code Pattern**:
```python
while order.validation_attempts < max_validation_attempts:
    order.validation_attempts += 1

    customer_result = await verify_customer(...)
    if not customer_result.passed:
        continue  # LOOP BACK

    inventory_result = await check_inventory(...)
    if not inventory_result.passed:
        continue  # LOOP BACK

    payment_result = await verify_payment(...)
    if not payment_result.passed:
        continue  # LOOP BACK

    # All passed - exit loop
    break
```

### Phase 2: Fulfillment Loop (LOOP 2)

**Purpose**: Pick and package items with quality assurance

**Activities**:
- `2.1 pick_items` - Warehouse picking operation

**Loop Behavior**:
- If items picked incorrectly → Loop back to 2.1
- Contains **NESTED LOOP 2A** for packaging

**Code Pattern**:
```python
while fulfillment_attempt < max_fulfillment_attempts:
    fulfillment_attempt += 1

    pick_result = await pick_items(...)
    if not pick_result.passed:
        continue  # LOOP BACK to picking

    # Enter nested packaging loop
    # (see Loop 2A below)

    # If packaging succeeds, exit fulfillment loop
    break
```

#### Nested Loop 2A: Packaging Quality Loop

**Purpose**: Ensure package meets quality standards before shipping

**Activities**:
- `2.2.1 pack_items_in_box` - Physical packing
- `2.2.2 seal_package` - Seal the box
- `2.2.3 quality_check_package` - QA inspection

**Loop Behavior**:
- If quality fails → Loop back to 2.2.1 (repack)
- If quality fails max times → Loop back to LOOP 2 (re-pick items)
- If quality passes → Continue to label printing

**Code Pattern**:
```python
# NESTED LOOP inside fulfillment loop
while packaging_attempt < max_packaging_attempts:
    packaging_attempt += 1

    package = await pack_items_in_box(...)
    package = await seal_package(...)
    quality = await quality_check_package(...)

    if not quality.passed:
        continue  # NESTED LOOP BACK to repacking

    # Quality passed - exit nested loop
    break

if not packaging_complete:
    continue  # LOOP BACK to parent (LOOP 2 - re-pick)
```

**Final Activity**:
- `2.3 print_shipping_label` - Generate tracking number

### Phase 3: Delivery Loop (LOOP 3)

**Purpose**: Attempt delivery with customer notification on failures

**Activities**:
- `3.1 assign_carrier` - Choose shipping carrier (once)
- `3.2 attempt_delivery` - Deliver package
- `3.3 notify_customer_delivery_failed` - Alert on failure
- `3.4 confirm_delivery` - Success confirmation
- `3.5 process_delivery_failure` - Handle final failure

**Loop Behavior**:
- If delivery fails & retry recommended → Loop back to 3.2
- Up to 3 delivery attempts
- Success rate increases: 40% → 70% → 100%

**Code Pattern**:
```python
shipment.carrier = await assign_carrier(...)  # Once, before loop

while shipment.attempts < max_delivery_attempts:
    shipment.attempts += 1

    delivery_result = await attempt_delivery(...)

    if delivery_result.delivered:
        break  # Success - exit loop

    # Delivery failed
    await notify_customer(...)

    if delivery_result.retry_recommended:
        continue  # LOOP BACK to retry delivery

# After loop - check outcome
if delivered:
    await confirm_delivery(...)
else:
    await process_delivery_failure(...)
```

## Visual Diagram

See `workflow_diagram.md` for complete Mermaid flowcharts showing:
- Full detailed workflow with all decision points
- Simplified loop structure
- Activity summary table

## Running the Example

### Prerequisites

1. **Start Temporal Server**:
   ```bash
   temporal server start-dev
   ```

2. **Navigate to directory**:
   ```bash
   cd MY/0_simple/workflow_loop
   ```

### Execute Workflow

```bash
python complex_multi_loop.py
```

### Expected Output

The workflow will demonstrate:
1. **Validation Loop**: 1-2 iterations
   - Customer verification (low credit score triggers manual check)
   - Possible inventory/payment retries
2. **Fulfillment Loop**: 1-2 iterations
   - Possible picking retry
   - **Nested Packaging Loop**: 1-2 iterations within each fulfillment attempt
3. **Delivery Loop**: 1-3 iterations
   - Progressive success probability

### Sample Output Structure

```
======================================================================
STARTING COMPLEX ORDER FULFILLMENT WORKFLOW
Order ID: ORD-2024-001
Customer: John Doe
Items: 3
Total: $340.0
======================================================================

▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
PHASE 1: ORDER VALIDATION (LOOP 1)
▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼

┌─ VALIDATION LOOP - Attempt 1 ─┐
│ Step 1.1: Verifying customer...
│ ✗ Customer verification failed: ['Customer needs manual verification']
│ ↻ LOOP BACK - Retrying validation...

┌─ VALIDATION LOOP - Attempt 2 ─┐
│ Step 1.1: Verifying customer...
│ Step 1.2: Checking inventory...
│ Step 1.3: Verifying payment...
│ ✓ All validations PASSED!

✓ PHASE 1 COMPLETE - Order validated in 2 attempt(s)

[... continues through all phases ...]
```

## View in Temporal UI

1. **Open**: http://localhost:8233
2. **Find workflow**: `complex-multi-loop-workflow`
3. **Examine**:
   - Event history showing all activity executions
   - How many times each activity ran
   - Loop iterations clearly visible in timeline
   - Activity retry patterns

## Key Implementation Patterns

### 1. Loop State Management

```python
# Track attempts across loop iterations
order.validation_attempts = 0  # Initialize

while order.validation_attempts < max_attempts:
    order.validation_attempts += 1  # Increment each iteration
    # ... execute activities ...
```

### 2. Early Exit on Success

```python
# Use break to exit when condition met
if result.passed:
    break  # Exit loop immediately
# Otherwise, continue loops back to start
```

### 3. Nested Loop with Parent Fallback

```python
# Outer loop
while outer_attempt < max_outer:
    outer_attempt += 1

    # Inner nested loop
    inner_success = False
    while inner_attempt < max_inner:
        inner_attempt += 1
        result = await activity(...)

        if result.ok:
            inner_success = True
            break  # Exit inner loop

    if not inner_success:
        continue  # LOOP BACK to outer loop start

    # Inner loop succeeded, continue outer loop flow
    break  # Exit outer loop
```

### 4. Progressive Retry Logic

```python
# Different behavior based on attempt number
success_rates = {1: 0.4, 2: 0.7, 3: 1.0}
success_rate = success_rates.get(attempt, 1.0)

if random.random() < success_rate:
    return Success()
```

### 5. Max Attempts Protection

```python
# Always check max attempts to prevent infinite loops
if attempt >= max_attempts:
    workflow.logger.error(f"Max attempts reached")
    return f"Failed after {max_attempts} attempts"
```

## Randomization for Testing

The workflow uses randomized failures to simulate real-world scenarios:

| Activity | Failure Probability | Recovery |
|----------|-------------------|----------|
| Customer Verification | High if credit < 600 | Manual approval on retry |
| Inventory Check | 40% on attempt 1 | Resolved on attempt 2+ |
| Payment Verification | 30% on attempt 1 | Resolved on attempt 2+ |
| Item Picking | 20% on attempt 1 | Corrected on retry |
| Package Quality | 30% on attempt 1 | Repackaging fixes |
| Delivery Attempt 1 | 60% fail rate | 40% success |
| Delivery Attempt 2 | 30% fail rate | 70% success |
| Delivery Attempt 3 | 0% fail rate | 100% success |

## Real-World Adaptations

### Remove Randomization for Production

Replace random failures with actual business logic:

```python
# Example: Replace random inventory check
@activity.defn
def check_inventory(items: List[OrderItem], attempt: int) -> ValidationResult:
    # Real implementation
    inventory_db = connect_to_inventory_system()

    for item in items:
        available = inventory_db.get_stock(item.sku)
        if available < item.quantity:
            return ValidationResult(
                passed=False,
                issues=[f"Insufficient stock for {item.sku}"],
                retry_possible=True
            )

    return ValidationResult(passed=True)
```

### Add Human-in-the-Loop

For manual verification steps:

```python
# Wait for human approval
approval = await workflow.execute_activity(
    request_manual_approval,
    customer,
    start_to_close_timeout=timedelta(hours=24),  # Long timeout
)

if not approval.approved:
    continue  # Loop back
```

### Configure Loop Parameters

```python
# Make max attempts configurable
@dataclass
class WorkflowConfig:
    max_validation_attempts: int = 3
    max_fulfillment_attempts: int = 3
    max_packaging_attempts: int = 3
    max_delivery_attempts: int = 3

@workflow.defn
class ComplexMultiLoopWorkflow:
    @workflow.run
    async def run(self, order: Order, config: WorkflowConfig = None):
        config = config or WorkflowConfig()
        # Use config.max_validation_attempts instead of hardcoded value
```

## Loop Debugging Tips

### 1. Enhanced Logging

```python
workflow.logger.info(
    f"Loop iteration {attempt}/{max_attempts} - "
    f"State: {current_state} - "
    f"Last error: {last_error}"
)
```

### 2. Loop Metrics

```python
# Track loop statistics
loop_stats = {
    "validation_loops": order.validation_attempts,
    "fulfillment_loops": fulfillment_attempt,
    "packaging_loops": packaging_attempt,
    "delivery_loops": shipment.attempts
}

workflow.logger.info(f"Loop statistics: {loop_stats}")
```

### 3. State Snapshots

```python
# Log state before each loop iteration
workflow.logger.info(f"Loop state snapshot: {json.dumps(dataclasses.asdict(order))}")
```

## Common Issues and Solutions

### Issue: Infinite Loop

**Symptom**: Workflow never completes

**Solution**:
- Always have `max_attempts` check
- Ensure loop condition can become False
- Add timeout to workflow execution

```python
# Bad - no max attempts
while not success:
    result = await activity(...)
    success = result.ok

# Good - with max attempts
attempt = 0
while not success and attempt < max_attempts:
    attempt += 1
    result = await activity(...)
    success = result.ok
```

### Issue: State Not Persisting Across Loop Iterations

**Symptom**: Loop always sees initial state

**Solution**: Update state before `continue`

```python
# Bad - state not updated
while attempt < max_attempts:
    result = await activity(data)
    if not result.ok:
        continue  # data is unchanged

# Good - state updated
while attempt < max_attempts:
    result = await activity(data)
    if not result.ok:
        data = apply_corrections(result.feedback)
        continue  # data has corrections
```

### Issue: Nested Loop Doesn't Affect Parent

**Symptom**: Nested loop failures don't trigger parent loop retry

**Solution**: Check nested loop outcome

```python
# After nested loop
if not nested_loop_success:
    continue  # Loop back in parent loop
```

## Performance Considerations

### Activity Timeouts

```python
# Short timeout for fast operations
await workflow.execute_activity(
    quick_check,
    data,
    start_to_close_timeout=timedelta(seconds=10),
)

# Long timeout for slow operations (delivery, manual approval)
await workflow.execute_activity(
    attempt_delivery,
    shipment,
    start_to_close_timeout=timedelta(minutes=30),
)
```

### Parallel Execution (Where Possible)

```python
# If validations are independent, run in parallel
customer_task = workflow.execute_activity(verify_customer, ...)
inventory_task = workflow.execute_activity(check_inventory, ...)
payment_task = workflow.execute_activity(verify_payment, ...)

# Wait for all
customer_result = await customer_task
inventory_result = await inventory_task
payment_result = await payment_task

# Then check results and loop if needed
```

### Wait Between Retries

```python
# Add delay before retry to avoid hammering systems
if not result.passed:
    workflow.logger.info("Waiting before retry...")
    await asyncio.sleep(2)  # 2 second delay
    continue
```

## Testing Strategy

### Unit Test Individual Loop Phases

```python
async def test_validation_loop():
    # Mock activities
    # Test with various failure scenarios
    # Verify correct number of retries
```

### Integration Test Full Workflow

```python
async def test_full_workflow_success_path():
    # All activities succeed on first try
    # Verify single iteration per loop

async def test_full_workflow_with_retries():
    # Configure activities to fail initially
    # Verify loop retries work correctly

async def test_full_workflow_max_attempts():
    # Configure activities to always fail
    # Verify workflow fails gracefully after max attempts
```

## Next Steps

1. **Modify loop conditions** - Change failure rates, thresholds
2. **Add more activities** - Expand phases with additional steps
3. **Implement real integrations** - Replace mocks with actual API calls
4. **Add more nested loops** - Create deeper nesting levels
5. **Human-in-the-loop** - Add manual approval activities
6. **Metrics & monitoring** - Track loop iterations in production

## Related Examples

- `simple_loop.py` - Basic single loop concept
- `loop_with_retry.py` - Document processing with retry
- `workflow_diagram.md` - Visual diagrams of this workflow
