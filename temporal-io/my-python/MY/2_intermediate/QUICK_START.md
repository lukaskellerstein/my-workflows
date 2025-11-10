# Quick Start Guide - 30 Second Setup

Get any project running in 30 seconds!

## 1. Choose Your Project

```bash
cd /home/lukas/Projects/Github/temporalio/MY_PROJECTS/2_intermediate

# Option 1: E-commerce (Signals + Queries)
cd 1_ecommerce_order_processing

# Option 2: HR Approval (Updates)
cd 2_hr_approval_slack

# Option 3: Marketing (User Actor)
cd 3_marketing_campaign_user_actor
```

## 2. One Command Setup

```bash
# Setup + start worker in one command
uv venv && source .venv/bin/activate && uv sync && uv run python worker.py
```

## 3. In Another Terminal

```bash
# Start API
cd [same-project-directory]
source .venv/bin/activate
uv run python api.py
```

## 4. Test It!

### Project 1 - E-commerce (Port 8000)
```bash
# Create order
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"C001","items":[{"product_id":"P1","product_name":"Laptop","quantity":1,"price":999}],"shipping_address":"123 Main","shipping_city":"SF","shipping_postal_code":"94102","shipping_country":"USA"}'

# Get the order_id from response, then:
# Confirm payment
curl -X POST http://localhost:8000/orders/[ORDER_ID]/payment \
  -H "Content-Type: application/json" \
  -d '{"transaction_id":"TXN123","amount":999,"payment_method":"card"}'

# Check status
curl http://localhost:8000/orders/[ORDER_ID]/status
```

### Project 2 - HR Approval (Port 8001)
```bash
# Create request
curl -X POST http://localhost:8001/requests \
  -H "Content-Type: application/json" \
  -d '{"employee_id":"E001","employee_name":"John","request_type":"time_off","title":"Vacation","description":"Beach trip","priority":"medium","start_date":"2025-03-01T00:00:00","end_date":"2025-03-10T00:00:00"}'

# Get the request_id from response, then:
# Manager approves
curl -X POST http://localhost:8001/requests/[REQUEST_ID]/manager-approval \
  -H "Content-Type: application/json" \
  -d '{"approver_id":"M001","approver_name":"Sarah","approved":true,"comments":"Approved!"}'

# HR approves
curl -X POST http://localhost:8001/requests/[REQUEST_ID]/hr-approval \
  -H "Content-Type: application/json" \
  -d '{"approver_id":"HR001","approver_name":"Linda","approved":true,"comments":"Approved!"}'
```

### Project 3 - Marketing (Port 8002)
```bash
# Init user actor
curl -X POST http://localhost:8002/users/USER-001/init \
  -H "Content-Type: application/json" \
  -d '{"user_id":"USER-001","max_messages_per_day":3}'

# Launch campaign
curl -X POST http://localhost:8002/campaigns/launch \
  -H "Content-Type: application/json" \
  -d '{"campaign_id":"C001","campaign_name":"Sale","campaign_type":"email","priority":"high","message_content":"50% off!","target_user_ids":["USER-001"]}'

# Check user state
curl http://localhost:8002/users/USER-001/state
```

## 5. View in Temporal UI

Open browser: http://localhost:8233

## That's it! 🎉

Now read the project README for detailed explanations.
