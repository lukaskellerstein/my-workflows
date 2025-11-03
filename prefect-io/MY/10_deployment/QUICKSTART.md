# Quick Start Guide - Server-Based Workflows

This guide will get you up and running with Prefect server deployments in under 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Project dependencies installed (`uv sync`)
- Basic understanding of Prefect flows (complete `0_simple/` first)

## 🚀 5-Minute Quick Start

### Step 1: Start Prefect Server (30 seconds)

```bash
# From project root
cd 10_server

# Start server with Docker Compose
docker-compose up -d

# Verify it's running
docker-compose ps
```

Expected output:
```
NAME               IMAGE                         STATUS
prefect-server     prefecthq/prefect:3-latest   Up
prefect-postgres   postgres:15-alpine            Up (healthy)
```

### Step 2: Configure Client (10 seconds)

```bash
# Point client to Docker server
export PREFECT_API_URL="http://localhost:4200/api"

# Verify configuration
uv run prefect config view | grep PREFECT_API_URL
```

Expected output:
```
PREFECT_API_URL='http://localhost:4200/api'
```

### Step 3: Deploy a Flow (1 minute)

Open a terminal and run:

```bash
# Deploy simple hello flow (will block)
uv run 10_server/01_simple_deployment.py
```

You should see:
```
Simple Deployment Example
============================================================
This will deploy the flow to your Prefect server.
...
```

**Keep this terminal running!** The deployment serves the flow.

### Step 4: View in UI (30 seconds)

1. Open browser: http://localhost:4200
2. Navigate to: **Deployments**
3. Find: **simple-hello**

You should see your deployed flow!

### Step 5: Trigger the Flow (1 minute)

**Option A - Via UI (Easiest):**

1. Click on **simple-hello** deployment
2. Click **Run** button (top right)
3. Click **Run** again to confirm
4. Navigate to **Flow Runs** to see execution
5. Click on the run to see logs and results

**Option B - Via API:**

Open a **new terminal** (keep deployment running) and run:

```bash
# Make sure API URL is set
export PREFECT_API_URL="http://localhost:4200/api"

# Trigger flow via API
uv run 10_server/04_trigger_via_api.py
```

### Step 6: View Results (30 seconds)

In the UI:
1. Go to **Flow Runs**
2. Click on the latest run
3. View the **Logs** tab to see execution details
4. View the **Graph** tab to see the flow visualization

## 🎯 What You Just Did

1. ✅ Started production-grade Prefect server with PostgreSQL
2. ✅ Deployed a flow to the server
3. ✅ Triggered flow execution via UI or API
4. ✅ Monitored execution in real-time

## 🔄 Key Differences from Direct Execution

### Direct Execution (Previous Examples)
```python
# Flow runs immediately, uses ephemeral server
my_flow()
```

### Server-Based Execution (This Section)
```python
# Flow is deployed, can be triggered multiple times
my_flow.serve(name="my-deployment")
```

## 📋 What's Next?

### Try Scheduled Workflows

Stop the current deployment (Ctrl+C) and run:

```bash
uv run 10_server/02_scheduled_deployment.py
```

This flow runs automatically every 30 seconds. Watch the **Flow Runs** page to see automatic executions!

### Try Parameterized Flows

Stop and run:

```bash
uv run 10_server/03_parameterized_deployment.py
```

Then trigger with custom parameters:
- UI: Click deployment → Custom Run → Enter JSON parameters
- API: Modify `04_trigger_via_api.py` to pass different parameters

### Try Work Pools (Production Pattern)

```bash
# Deploy to work pool (returns immediately)
uv run 10_server/05_work_pool.py

# Start worker in another terminal
export PREFECT_API_URL="http://localhost:4200/api"
uv run prefect worker start --pool "my-pool"

# Trigger via UI or API
```

## 🛑 Cleanup

When done experimenting:

```bash
# Stop server (keeps data)
docker-compose stop

# Stop and remove (loses data)
docker-compose down

# Complete cleanup (removes volumes)
docker-compose down -v
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 4200
sudo lsof -i :4200

# Kill the process or change docker-compose.yml port
```

### "Connection refused" Error
```bash
# Check server is running
docker-compose ps

# Check logs
docker-compose logs prefect-server

# Restart server
docker-compose restart prefect-server
```

### Deployment Not Found
```bash
# Make sure deployment script is still running
# Check deployments list
uv run prefect deployment ls
```

## 📚 Learn More

- **Full Documentation**: See `README.md` in this folder
- **Prefect Deployments**: https://docs.prefect.io/v3/deploy
- **Docker Compose**: https://docs.docker.com/compose/

## 💡 Tips

1. **Keep Deployment Running**: Flows using `serve()` must keep running
2. **Multiple Terminals**: Use one for deployment, one for triggering
3. **View Logs**: Always check Flow Run logs in UI for debugging
4. **API URL**: Remember to set `PREFECT_API_URL` in each terminal
5. **UI is Your Friend**: The UI at http://localhost:4200 is invaluable

---

**Congratulations! 🎉**

You've successfully deployed and run workflows on a Prefect server. This is the foundation for production deployments, scheduling, and orchestration at scale.
