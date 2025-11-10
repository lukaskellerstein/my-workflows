# Troubleshooting Guide

Common issues and their solutions for all three projects.

## General Issues

### Issue: "Connection refused to localhost:7233"

**Symptom**: Worker or API can't connect to Temporal server

**Solution**:
```bash
# Start Temporal server
temporal server start-dev

# Check it's running
curl http://localhost:8233
# Should show Temporal UI
```

---

### Issue: "ModuleNotFoundError: No module named 'temporalio'"

**Symptom**: Python can't find Temporal SDK

**Solution**:
```bash
# Make sure you're in virtual environment
source .venv/bin/activate

# Install dependencies
uv sync

# Verify installation
uv run python -c "import temporalio; print(temporalio.__version__)"
```

---

### Issue: Worker starts but doesn't process workflows

**Symptom**: Workflow created but stays in "Running" state forever

**Common Causes**:

1. **Wrong task queue name**
   ```bash
   # Check worker task queue
   grep "task_queue=" worker.py

   # Should match workflow start:
   # Project 1: "order-processing-queue"
   # Project 2: "hr-approval-queue"
   # Project 3: "marketing-campaign-queue"
   ```

2. **Worker not running**
   ```bash
   # Make sure worker terminal is still running
   # You should see: "🚀 ... Worker started!"
   ```

3. **Wrong workflow registered**
   ```bash
   # Check worker.py has correct workflow class
   workflows=[YourWorkflow]
   ```

---

### Issue: "Workflow execution not found"

**Symptom**: Can't query/signal workflow

**Solutions**:

1. **Check workflow ID format**
   ```bash
   # Project 1: order-{order_id}
   # Example: order-ORD-20250131-143022

   # Project 2: approval-{request_id}
   # Example: approval-REQ-20250131-153022

   # Project 3: user-actor-{user_id}
   # Example: user-actor-USER-001
   ```

2. **Verify workflow was created**
   ```bash
   # Check Temporal UI
   http://localhost:8233

   # Search for workflow ID
   ```

3. **Workflow might have completed**
   ```bash
   # Queries work on completed workflows
   # Signals/Updates DON'T work on completed workflows
   ```

---

## Project 1: E-commerce

### Issue: Order stuck at "pending"

**Symptom**: Order created but never progresses

**Cause**: Waiting for payment signal

**Solution**:
```bash
# Send payment confirmation
curl -X POST http://localhost:8000/orders/{ORDER_ID}/payment \
  -H "Content-Type: application/json" \
  -d '{"transaction_id":"TXN123","amount":999.99,"payment_method":"card"}'
```

---

### Issue: "Payment timeout after 24 hours"

**Symptom**: Workflow completed with timeout error

**Solution**: This is expected behavior! Orders must be paid within 24 hours.

```python
# In workflows.py:
await workflow.wait_condition(
    lambda: self._payment_confirmed or self._should_cancel,
    timeout=timedelta(hours=24)  # ← Timeout here
)
```

To change timeout, edit `workflows.py` and restart worker.

---

### Issue: Can't query completed order

**Symptom**: 404 error when querying

**Solution**: Queries SHOULD work on completed workflows. Check:

```bash
# Verify workflow ID is correct
curl http://localhost:8000/orders/{ORDER_ID}

# Check Temporal UI - is workflow there?
http://localhost:8233
```

---

## Project 2: HR Approval

### Issue: "Cannot submit manager approval. Current status: manager_approved"

**Symptom**: Update validator rejects request

**Solution**: This is correct behavior! Manager already approved.

```python
# Validator ensures manager only approves once
@workflow.update(name="submit_manager_approval")
def validate_manager_approval(self, decision: ApprovalDecision) -> None:
    if self._manager_responded:
        raise ApplicationError("Manager has already submitted approval")
```

**Cannot re-approve**. Create new request to test again.

---

### Issue: "Cannot submit HR approval. Manager must approve first."

**Symptom**: Trying to HR approve before manager

**Solution**: This is correct! Multi-level approval enforced.

```bash
# Step 1: Manager approves first
curl -X POST http://localhost:8001/requests/{REQ_ID}/manager-approval ...

# Step 2: Then HR can approve
curl -X POST http://localhost:8001/requests/{REQ_ID}/hr-approval ...
```

---

### Issue: Slack integration not working

**Symptom**: No messages in Slack

**Solution**: Demo mode! By default, messages are logged only.

```bash
# Check worker logs - you'll see:
# "Slack message: ..."

# To enable real Slack:
1. Copy .env.example to .env
2. Add your Slack tokens
3. Restart worker
```

---

## Project 3: Marketing

### Issue: "User actor not found"

**Symptom**: Campaign can't send to user

**Solution**: Initialize User Actor first!

```bash
# Must initialize before launching campaigns
curl -X POST http://localhost:8002/users/USER-001/init \
  -H "Content-Type: application/json" \
  -d '{"user_id":"USER-001","max_messages_per_day":3}'

# Then launch campaign
curl -X POST http://localhost:8002/campaigns/launch ...
```

---

### Issue: All messages skipped due to frequency cap

**Symptom**: Campaign completes but users_sent = 0

**Check frequency status**:
```bash
curl http://localhost:8002/users/USER-001/state
```

**Solutions**:

1. **Daily cap reached**
   ```bash
   # Wait until tomorrow, or increase cap:
   curl -X POST http://localhost:8002/users/USER-001/init \
     -d '{"user_id":"USER-001","max_messages_per_day":10}'
   ```

2. **Min hours between messages**
   ```bash
   # Wait 2 hours (default), or reduce:
   curl -X POST http://localhost:8002/users/USER-001/init \
     -d '{"user_id":"USER-001","min_hours_between_messages":0}'
   ```

3. **User opted out**
   ```bash
   # Opt back in
   curl -X POST http://localhost:8002/users/USER-001/opt-in \
     -d '{"channel":"email"}'
   ```

---

### Issue: User Actor workflow not found after initialization

**Symptom**: Just created User Actor, but can't query it

**Solution**: Wait a moment for workflow to start

```bash
# If just initialized, wait 1-2 seconds

# Verify it's running in Temporal UI
http://localhost:8233
# Search for: user-actor-USER-001
```

---

### Issue: Campaign workflow stuck

**Symptom**: Campaign in "Running" state forever

**Check**:
```bash
# Get campaign progress
curl http://localhost:8002/campaigns/CAMP-001/progress

# Check target users exist
# Each user needs User Actor initialized
```

---

## API Issues

### Issue: API returns "Temporal client not initialized"

**Symptom**: 500 error on all endpoints

**Solution**: API not fully started

```bash
# Wait for startup message:
# "✅ Connected to Temporal server"

# If not appearing, check Temporal server is running:
temporal server start-dev
```

---

### Issue: Port already in use

**Symptom**: "Address already in use" when starting API

**Solution**: Different ports for each project

```bash
# Project 1: Port 8000
# Project 2: Port 8001
# Project 3: Port 8002

# If port still in use:
lsof -i :8000
kill -9 {PID}

# Or change port:
uvicorn api:app --port 8003
```

---

## Debugging Tips

### View Workflow History

```bash
# Temporal UI
http://localhost:8233

# Or CLI
temporal workflow show --workflow-id "order-ORD-20250131-143022"
```

### View Worker Logs

```bash
# Worker terminal shows:
# - Activity executions
# - Workflow logs
# - Error messages

# Look for:
workflow.logger.info("...")  # Your log messages
activity.logger.info("...")  # Activity logs
```

### Check Workflow State

```bash
# Project 1
curl http://localhost:8000/orders/{ORDER_ID}

# Project 2
curl http://localhost:8001/requests/{REQUEST_ID}

# Project 3
curl http://localhost:8002/users/{USER_ID}/state
```

### Test Workflow Logic

```python
# Add temporary log in workflow
workflow.logger.info(f"Current state: {self._status}")
workflow.logger.info(f"Payment info: {self._payment_info}")

# Restart worker to see logs
```

---

## Performance Issues

### Issue: Workflows slow to start

**Possible causes**:

1. **Too many workflows**
   ```bash
   # Check Temporal UI - how many workflows running?
   # Temporal handles millions, but check worker resources
   ```

2. **Activity timeouts too long**
   ```python
   # Reduce timeouts for testing:
   start_to_close_timeout=timedelta(seconds=5)  # Instead of 30
   ```

3. **Worker overloaded**
   ```bash
   # Start multiple workers (different terminals)
   uv run python worker.py
   # Temporal auto-distributes load
   ```

---

### Issue: High memory usage

**Cause**: Too many workflows in memory

**Solution**: Continue-As-New (already implemented in User Actor)

```python
# User Actor automatically restarts every 30 days
if self._days_running >= 30:
    workflow.continue_as_new(user_id, self._frequency_cap)
```

---

## Testing Tips

### Reset Everything

```bash
# Stop Temporal server (Ctrl+C)
# Delete data
rm -rf /tmp/temporal_*

# Restart fresh
temporal server start-dev
```

### Quick Test Script

```bash
#!/bin/bash
# test.sh - Test Project 1

# Create order
ORDER_RESPONSE=$(curl -s -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"C001","items":[{"product_id":"P1","product_name":"Test","quantity":1,"price":10}],"shipping_address":"123 Main","shipping_city":"SF","shipping_postal_code":"94102","shipping_country":"USA"}')

ORDER_ID=$(echo $ORDER_RESPONSE | jq -r '.order_id')
echo "Order ID: $ORDER_ID"

# Confirm payment
curl -X POST http://localhost:8000/orders/$ORDER_ID/payment \
  -H "Content-Type: application/json" \
  -d '{"transaction_id":"TXN123","amount":10,"payment_method":"card"}'

# Check status
curl http://localhost:8000/orders/$ORDER_ID/status
```

---

## Still Having Issues?

1. **Check Temporal UI**: http://localhost:8233
   - See workflow execution
   - Check event history
   - Look for errors

2. **Check Worker Logs**: Activity and workflow logs

3. **Verify Setup**:
   ```bash
   # Temporal running?
   curl http://localhost:8233

   # Worker running?
   ps aux | grep "python worker.py"

   # API running?
   curl http://localhost:8000/health  # Project 1
   curl http://localhost:8001/health  # Project 2
   curl http://localhost:8002/health  # Project 3
   ```

4. **Check README**: Each project has detailed documentation

5. **Start Fresh**:
   ```bash
   # Kill everything
   pkill -f "python worker.py"
   pkill -f "uvicorn api:app"

   # Restart in order:
   # 1. Temporal server
   # 2. Worker
   # 3. API
   ```

---

## Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `ApplicationError: Wrong status` | Update validator rejected | Check workflow state, can't repeat operation |
| `TimeoutError` | Workflow condition timeout | Expected for payment timeout, send signal |
| `WorkflowNotFoundError` | Workflow doesn't exist | Check workflow ID format, verify creation |
| `Connection refused` | Can't reach Temporal | Start Temporal server |
| `No module named 'temporalio'` | SDK not installed | `uv sync` |

---

Need more help? Check:
- [Temporal Community](https://community.temporal.io)
- [Temporal Documentation](https://docs.temporal.io)
- Project-specific READMEs
