# E-commerce Order Processing - Signals & Queries Demo

This project demonstrates **Temporal Signals and Queries** through a real-world e-commerce order processing system.

## 🎯 What You'll Learn

### Signals (Write Operations)
- **confirm_payment**: External payment gateway sends payment confirmation
- **cancel_order**: Customer or admin cancels the order
- Signals modify workflow state asynchronously
- Recorded in event history

### Queries (Read Operations)
- **get_order_status**: Get current order status
- **get_full_state**: Get complete order information
- **get_estimated_delivery**: Get delivery ETA
- Queries are read-only and NOT recorded in history
- Can query even completed workflows

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   REST API  │─────▶│   Temporal   │◀─────│  Workflow       │
│  (FastAPI)  │      │   Server     │      │  (Order Logic)  │
└─────────────┘      └──────────────┘      └─────────────────┘
                             │                       │
                             │                       ▼
                             │              ┌─────────────────┐
                             └─────────────▶│   Activities    │
                                            │ (Business Logic)│
                                            └─────────────────┘
```

## 🚀 Setup

```bash
# Navigate to project directory
cd /home/lukas/Projects/Github/temporalio/MY_PROJECTS/2_intermediate/1_ecommerce_order_processing

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv sync
```

## 📋 Prerequisites

Make sure Temporal server is running:
```bash
temporal server start-dev
```

## 🎮 Usage

### 1. Start the Worker

In terminal 1:
```bash
source .venv/bin/activate
uv run python worker.py
```

### 2. Start the REST API

In terminal 2:
```bash
source .venv/bin/activate
uv run uvicorn api:app --reload
```

The API will be available at http://localhost:8000

### 3. Interact with Orders

#### Create a New Order

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-001",
    "items": [
      {
        "product_id": "PROD-123",
        "product_name": "Laptop",
        "quantity": 1,
        "price": 999.99
      }
    ],
    "shipping_address": "123 Main St",
    "shipping_city": "San Francisco",
    "shipping_postal_code": "94102",
    "shipping_country": "USA"
  }'
```

Response:
```json
{
  "order_id": "ORD-20250131-143022",
  "workflow_id": "order-ORD-20250131-143022",
  "status": "pending",
  "total_amount": 999.99,
  "message": "Order created successfully. Awaiting payment confirmation."
}
```

#### Query Order Status (READ-ONLY)

```bash
curl http://localhost:8000/orders/ORD-20250131-143022/status
```

Response:
```json
{
  "order_id": "ORD-20250131-143022",
  "status": "pending"
}
```

#### Confirm Payment (SIGNAL - WRITE)

```bash
curl -X POST http://localhost:8000/orders/ORD-20250131-143022/payment \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TXN-12345",
    "amount": 999.99,
    "payment_method": "credit_card"
  }'
```

#### Get Full Order Details (QUERY - READ)

```bash
curl http://localhost:8000/orders/ORD-20250131-143022
```

Response:
```json
{
  "order_id": "ORD-20250131-143022",
  "customer_id": "CUST-001",
  "status": "shipped",
  "total_amount": 999.99,
  "payment_info": {
    "transaction_id": "TXN-12345",
    "amount": 999.99,
    "payment_method": "credit_card",
    "timestamp": "2025-01-31T14:30:45"
  },
  "shipment_info": {
    "tracking_number": "FEDEX-ORD-20250131-143022-PKG-123",
    "provider": "fedex",
    "estimated_delivery": "2025-02-03T14:30:45",
    "shipped_at": "2025-01-31T14:31:00"
  },
  "created_at": "2025-01-31T14:30:22",
  "updated_at": "2025-01-31T14:31:00",
  "estimated_delivery": "2025-02-03T14:30:45",
  "cancellation_reason": null
}
```

#### Cancel Order (SIGNAL - WRITE)

```bash
curl -X DELETE http://localhost:8000/orders/ORD-20250131-143022 \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Customer requested cancellation"
  }'
```

## 🔍 Workflow Flow

1. **Order Created** → Status: `pending`
   - Inventory reserved
   - Email sent: "Order Received"
   - **Waits for payment signal** (24-hour timeout)

2. **Payment Confirmed (Signal)** → Status: `payment_confirmed`
   - Payment processed
   - Email sent: "Payment Confirmed"

3. **Preparing Shipment** → Status: `preparing`
   - Items packaged
   - Shipment prepared

4. **Order Shipped** → Status: `shipped`
   - Tracking number generated
   - Email sent: "Order Shipped"

5. **Order Delivered** → Status: `delivered`
   - Email sent: "Order Delivered"

### Cancellation Flow (Compensation)

If cancelled before shipment:
- Refund payment (if paid)
- Release inventory
- Email sent: "Order Cancelled"

## 🎓 Key Concepts Demonstrated

### Signals vs Queries

| Feature | Signals | Queries |
|---------|---------|---------|
| Purpose | **Write** - modify state | **Read** - get state |
| Async/Sync | Asynchronous | Synchronous |
| Recorded | YES (in event history) | NO |
| Side effects | Can modify state | Read-only |
| When workflow closed | ❌ Cannot signal | ✅ Can query |

### Why Use Signals?

1. **External Event Integration**: Payment gateways, webhooks, user actions
2. **Asynchronous Updates**: Don't block external systems
3. **Durable**: Signals are recorded and replayed
4. **Human-in-the-Loop**: User approvals, confirmations

### Why Use Queries?

1. **Real-time Monitoring**: Check workflow progress
2. **No Side Effects**: Safe to call repeatedly
3. **Works on Closed Workflows**: Historical data access
4. **Fast**: Direct read without workflow execution

## 📊 View in Temporal UI

Open http://localhost:8233 to see:
- Workflow execution history
- All signals sent (recorded as events)
- Queries executed (not recorded)
- Activity executions
- Retry attempts

## 🧪 Testing Scenarios

### Happy Path
1. Create order → Check status (query) → Confirm payment (signal) → Check status → Wait for delivery

### Cancellation Before Payment
1. Create order → Cancel immediately (signal) → Check status → Verify refund

### Cancellation After Payment
1. Create order → Confirm payment → Cancel (signal) → Check status → Verify refund + inventory release

### Query Completed Workflow
1. Wait for order to complete
2. Query status even after workflow is done
3. Demonstrates queries work on closed workflows

## 💡 Best Practices Demonstrated

1. **Deterministic Workflow Code**: No direct I/O in workflows
2. **Activities for Business Logic**: Payment, shipping, emails
3. **Compensation Logic**: Automatic refunds and inventory release
4. **Timeout Handling**: 24-hour payment timeout
5. **State Queries**: Multiple query methods for different use cases
6. **Signal Handling**: Wait conditions with timeouts

## 🔗 API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
