# 10 - Server-Based Workflows

This folder demonstrates how to work with Prefect workflows when running a Prefect server locally via Docker Compose.

## 🔄 Direct Execution vs Server-Based Execution

### Direct Execution (All Previous Examples)
```python
@flow
def my_flow():
    return "result"

# Runs immediately, uses ephemeral server
if __name__ == "__main__":
    my_flow()
```
- Flow executes immediately when script runs
- Prefect starts temporary local server for tracking
- Server shuts down when script completes
- Good for: development, testing, simple scripts

### Server-Based Execution (This Section)
```python
@flow
def my_flow():
    return "result"

# Deploy to server
if __name__ == "__main__":
    my_flow.serve(name="my-deployment")
```
- Flow is deployed to persistent Prefect server
- Can be scheduled or triggered via UI/API
- Server keeps running independently
- Good for: production, scheduling, orchestration

## 🚀 Quick Start

### 1. Start Prefect Server with Docker Compose

```bash
cd 10_server

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f prefect-server

# Access UI
open http://localhost:4200
```

### 2. Configure Client to Use Docker Server

```bash
# Point to Docker Compose server
export PREFECT_API_URL="http://localhost:4200/api"

# Verify connection
uv run prefect config view
```

### 3. Run Deployment Examples

```bash
# Simple deployment (keeps running)
uv run 10_server/01_simple_deployment.py

# In another terminal, trigger via UI or API
uv run 10_server/04_trigger_via_api.py
```

## 📁 Examples

### 01_simple_deployment.py
**Concept**: Basic deployment using `flow.serve()`
- Deploys flow to server
- Serves flow indefinitely (blocks)
- Can be triggered via UI or API

**Use Case**: Simple continuous service

### 02_scheduled_deployment.py
**Concept**: Scheduled workflow execution
- Runs on cron schedule
- Interval-based scheduling
- RRule for complex patterns

**Use Case**: ETL jobs, reports, batch processing

### 03_parameterized_deployment.py
**Concept**: Deployments with parameters
- Accept runtime parameters
- Default values
- Type validation

**Use Case**: Dynamic workflows, user inputs

### 04_trigger_via_api.py
**Concept**: Programmatically trigger flows
- REST API interaction
- Pass parameters
- Monitor execution

**Use Case**: External system integration, webhooks

### 05_work_pool.py
**Concept**: Work pools and workers
- Separate deployment from execution
- Scale workers independently
- Process-based execution

**Use Case**: Production deployments, scaling

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Docker Compose Stack            │
├─────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐  │
│  │   Prefect    │    │  PostgreSQL  │  │
│  │    Server    │◄───┤   Database   │  │
│  │  Port: 4200  │    │  Port: 5432  │  │
│  └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────┘
         ▲                    ▲
         │                    │
    ┌────┴────────────────────┴─────┐
    │                                │
┌───┴───────┐              ┌────────┴──────┐
│   Flows   │              │   Workers     │
│  (serve)  │              │ (work pools)  │
└───────────┘              └───────────────┘
```

## 🔑 Key Concepts

### Deployments
A deployment is a server-side representation of a flow that can be:
- Scheduled to run automatically
- Triggered manually via UI
- Triggered via API calls
- Configured with parameters

### Work Pools
Work pools manage where and how flows execute:
- **Process pool**: Run in separate Python processes
- **Docker pool**: Run in Docker containers
- **Kubernetes pool**: Run in K8s pods

### Workers
Workers poll work pools for scheduled runs:
- Pull work from queue
- Execute flow runs
- Report results back to server

## 🎯 Common Patterns

### Pattern 1: Long-Running Service
```python
# Deployment that stays alive
my_flow.serve(name="my-service")
```

### Pattern 2: Scheduled Job
```python
# Run every hour
my_flow.serve(
    name="hourly-job",
    cron="0 * * * *"
)
```

### Pattern 3: On-Demand Execution
```python
# Deploy without schedule, trigger via API
my_flow.serve(name="on-demand")
```

### Pattern 4: Work Pool Deployment
```python
# Deploy to work pool, scale workers separately
my_flow.deploy(
    name="scalable-workflow",
    work_pool_name="my-pool"
)
```

## 🔄 Workflow Lifecycle

1. **Development**: Write flow locally, test with direct execution
2. **Deployment**: Deploy to server with `serve()` or `deploy()`
3. **Scheduling**: Configure schedule (optional)
4. **Execution**: Server triggers flow runs based on schedule/API
5. **Monitoring**: View results in UI, check logs
6. **Updates**: Redeploy with changes

## 🛠️ Management Commands

```bash
# List all deployments
uv run prefect deployment ls

# Inspect a deployment
uv run prefect deployment inspect "my-flow/my-deployment"

# Delete a deployment
uv run prefect deployment delete "my-flow/my-deployment"

# List flow runs
uv run prefect flow-run ls

# Cancel a flow run
uv run prefect flow-run cancel <run-id>

# Create work pool
uv run prefect work-pool create "my-pool" --type process

# Start worker
uv run prefect worker start --pool "my-pool"
```

## 🐳 Docker Compose Management

```bash
# Start services
docker-compose up -d

# Stop services (keeps data)
docker-compose stop

# Stop and remove (loses data)
docker-compose down

# Stop and remove with volumes (complete cleanup)
docker-compose down -v

# View logs
docker-compose logs -f

# Restart service
docker-compose restart prefect-server

# Check resource usage
docker-compose stats
```

## 🔍 Debugging

### Check Server Connection
```bash
export PREFECT_API_URL="http://localhost:4200/api"
uv run prefect config view
```

### View Server Logs
```bash
docker-compose logs -f prefect-server
```

### Access Database
```bash
docker-compose exec postgres psql -U prefect -d prefect
```

### Test API Connection
```bash
curl http://localhost:4200/api/health
```

## 📊 Comparison: Serve vs Deploy

| Feature | `flow.serve()` | `flow.deploy()` |
|---------|----------------|-----------------|
| Execution | In same process | Via work pool/worker |
| Scaling | Single instance | Multiple workers |
| Deployment | Blocks until Ctrl+C | Returns immediately |
| Use Case | Simple services | Production systems |
| Infrastructure | Minimal | Work pools required |

## 🎓 Learning Path

1. **Start Server**: `docker-compose up -d`
2. **Configure Client**: Set `PREFECT_API_URL`
3. **Simple Deployment**: Run `01_simple_deployment.py`
4. **Trigger Flow**: Use UI or `04_trigger_via_api.py`
5. **Add Schedule**: Modify deployment with cron
6. **Work Pools**: Create pool and worker
7. **Production**: Deploy to work pool

## 💡 Best Practices

1. **Use Environment Variables**: Store API URL, credentials
2. **Name Deployments Clearly**: Use descriptive, unique names
3. **Version Deployments**: Include version in name or tags
4. **Monitor Resources**: Check Docker stats regularly
5. **Backup Database**: Regular PostgreSQL backups
6. **Use Work Pools for Production**: Better isolation and scaling
7. **Test Locally First**: Direct execution before deployment
8. **Log Everything**: Use Prefect logging for observability

## 🚨 Troubleshooting

### "Connection refused" Error
```bash
# Check server is running
docker-compose ps

# Check API URL
echo $PREFECT_API_URL

# Should be: http://localhost:4200/api
```

### Deployment Not Appearing in UI
```bash
# Verify deployment was created
uv run prefect deployment ls

# Check server logs
docker-compose logs -f prefect-server
```

### Flow Run Stuck "Scheduled"
```bash
# Check if worker is running
uv run prefect worker start --pool "default"

# Or deployment is served
# Keep serve() script running
```

## 🔗 Related Concepts

- **Blocks**: Reusable configuration objects
- **Automations**: Event-driven flow triggering
- **Webhooks**: External system integration
- **Artifacts**: Store and visualize results
- **Notifications**: Alerts on flow state changes

## 📖 Additional Resources

- [Prefect Deployments Docs](https://docs.prefect.io/v3/deploy)
- [Work Pools Guide](https://docs.prefect.io/v3/deploy/dynamic-infra/push-runs-serverless)
- [Docker Deployment](https://docs.prefect.io/v3/deploy/infrastructure-concepts/docker)

---

**Next Steps**: After mastering server-based workflows, explore production deployment patterns, CI/CD integration, and Kubernetes orchestration.
