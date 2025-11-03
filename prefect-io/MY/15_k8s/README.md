# Kubernetes Flow Deployment Guide

This guide walks you through deploying a Prefect flow to Kubernetes using Terraform.

## Prerequisites

- Kubernetes cluster running with Prefect server (192.168.5.65:4200)
- Prefect worker deployed and connected to work pool "MyFirstWorkPool"
- Docker installed on your machine
- Terraform installed
- Docker Hub account (or another container registry)
- `uv` package manager installed ([installation guide](https://docs.astral.sh/uv/))

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│         Kubernetes Cluster                  │
│                                             │
│  ┌──────────────┐      ┌──────────────┐   │
│  │ Prefect      │      │ Prefect      │   │
│  │ Server       │◄─────┤ Worker       │   │
│  │ (port 4200)  │      │ (polling)    │   │
│  └──────────────┘      └──────┬───────┘   │
│                                │            │
│                                │ spawns     │
│                                ▼            │
│                        ┌──────────────┐    │
│                        │ Flow Pod     │    │
│                        │ (your image) │    │
│                        └──────────────┘    │
└─────────────────────────────────────────────┘
         ▲                        ▲
         │                        │
         │ terraform apply        │ docker push
         │                        │
    ┌────┴──────┐         ┌───────┴────┐
    │ Your PC   │         │ Docker Hub │
    └───────────┘         └────────────┘
```

## Step-by-Step Deployment

### Step 1: Test the Flow Locally (Optional)

Before building the Docker image, test the flow locally:

```bash
cd MY/15_k8s

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv sync

# Run the flow locally
uv run python flow.py
```

**Note**: This will generate a `uv.lock` file for reproducible builds.

### Step 2: Build the Docker Image

```bash
# Build the image
docker build -t lukaskellerstein/prefect-k8s-flow:latest .

# Optional: Test the image locally
docker run --rm lukaskellerstein/prefect-k8s-flow:latest python flow.py
```

### Step 3: Push to Docker Hub

Log in and push the image:

```bash
# Login to Docker Hub
docker login

# Push the image
docker push lukaskellerstein/prefect-k8s-flow:latest
```

**Note**: The image must be publicly accessible or you need to configure image pull secrets in Kubernetes.

### Step 4: Configure Terraform

Create your `terraform.tfvars` file:

```bash
cd terraform

# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

Update `terraform.tfvars`:

```hcl
prefect_api_url  = "http://192.168.5.65:4200/api"
docker_image     = "yourusername/prefect-k8s-flow:latest"  # Your actual image
work_pool_name   = "MyFirstWorkPool"
deployment_name  = "k8s-etl-deployment"

# Optional: Uncomment to add a schedule
# schedule_cron = "0 2 * * *"  # Daily at 2 AM UTC
```

### Step 5: Deploy with Terraform

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply the deployment
terraform apply
```

Type `yes` when prompted.

### Step 6: Verify Deployment

1. **Via Prefect UI**:

   - Open http://192.168.5.65:4200
   - Navigate to Deployments
   - You should see "k8s-etl-deployment"

2. **Via kubectl** (check if pods are created when flow runs):
   ```bash
   kubectl get pods -w
   ```

### Step 7: Run the Flow

**Option A: Via Prefect UI**

- Go to Deployments → k8s-etl-deployment
- Click "Run" → "Quick Run"

**Option B: Via API (curl)**

```bash
curl -X POST http://192.168.5.65:4200/api/deployments/name/k8s-etl-deployment/create_flow_run
```

### Step 8: Monitor Execution

Watch the flow run in real-time:

```bash
# Watch Kubernetes pods
kubectl get pods -w

# Check pod logs (replace POD_NAME with actual pod name)
kubectl logs -f <POD_NAME>
```

In Prefect UI:

- Go to Flow Runs
- Click on the latest run
- View logs and task execution

## File Structure

```
MY/15_k8s/
├── flow.py                 # Your flow code
├── pyproject.toml          # Project configuration (uv)
├── uv.lock                 # Dependency lock file (generated)
├── Dockerfile              # Docker image definition (uses uv)
├── terraform/
│   ├── provider.tf        # Terraform provider config
│   ├── variables.tf       # Variable definitions
│   ├── main.tf           # Deployment resource
│   ├── terraform.tfvars  # Your values (gitignored)
│   └── terraform.tfvars.example
└── README.md             # This file
```

## Common Issues & Solutions

### Issue: Image Pull Error

**Problem**: Pod shows `ImagePullBackOff` error

**Solutions**:

1. Ensure image is pushed to Docker Hub: `docker push yourusername/prefect-k8s-flow:latest`
2. Verify image name is correct in `terraform.tfvars`
3. If using private registry, configure image pull secrets

### Issue: Pod CrashLoopBackOff

**Problem**: Pod crashes immediately after starting

**Solutions**:

1. Check pod logs: `kubectl logs <pod-name>`
2. Verify PREFECT_API_URL is correct
3. Ensure worker can reach Prefect server

### Issue: Deployment Not Showing in UI

**Problem**: Terraform applies successfully but deployment not visible

**Solutions**:

1. Verify PREFECT_API_URL in `terraform.tfvars` matches your server
2. Check Terraform output for errors
3. Refresh Prefect UI

## Updating the Flow

When you make changes to `flow.py`:

```bash
# Rebuild the image
docker build -t yourusername/prefect-k8s-flow:latest .

# Push to Docker Hub
docker push yourusername/prefect-k8s-flow:latest

# Terraform will use the updated image automatically
# (if image_pull_policy is "Always")
```

No need to run `terraform apply` again unless you changed Terraform configuration.

## Scheduling

To add a schedule, edit `terraform.tfvars`:

```hcl
schedule_cron = "0 2 * * *"  # Daily at 2 AM UTC
```

Then run:

```bash
terraform apply
```

## Clean Up

To remove the deployment:

```bash
cd terraform
terraform destroy
```

## Next Steps

- **Add Parameters**: Modify `flow.py` to accept different parameters
- **Add Secrets**: Use Kubernetes secrets for sensitive data
- **Resource Limits**: Adjust CPU/memory in `main.tf` job_variables
- **Multiple Flows**: Create additional `.tf` files for more deployments
- **CI/CD**: Automate Docker build and Terraform apply in GitHub Actions

## Useful Commands

```bash
# View all deployments
kubectl get deployments

# View pods
kubectl get pods

# View pod logs
kubectl logs <pod-name>

# Describe pod for details
kubectl describe pod <pod-name>

# Port forward to Prefect UI (if needed)
kubectl port-forward svc/prefect-server 4200:4200
```

## References

- [Prefect Terraform Provider](https://registry.terraform.io/providers/PrefectHQ/prefect/latest/docs)
- [Prefect Kubernetes Guide](https://docs.prefect.io/v3/how-to-guides/deployment_infra/kubernetes)
- [Docker Hub](https://hub.docker.com/)
