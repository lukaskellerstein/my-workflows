# Kubernetes Deployment for Temporal Workers

This example demonstrates deploying a Temporal workflow worker to Kubernetes.

## Project Structure

```
MY/15_k8s/
├── worker/              # Worker project (runs in Kubernetes)
│   ├── worker.py       # Worker implementation
│   ├── Dockerfile      # Container image
│   ├── pyproject.toml  # Python dependencies (uv)
│   └── k8s/            # Kubernetes manifests
│       ├── configmap.yaml
│       └── deployment.yaml
│
├── starter/            # Starter project (runs locally)
│   ├── starter.py      # Workflow starter script
│   └── pyproject.toml  # Python dependencies (uv)
│
└── README.md          # This file
```

## Prerequisites

- Docker installed
- Docker Hub account
- Kubernetes cluster with kubectl configured
- Temporal server running at `192.168.5.65:7233`
- Python 3.11+ with `uv` installed

## Part 1: Build and Push Worker Image

### Step 1: Navigate to worker directory

```bash
cd MY/15_k8s/worker
```

### Step 2: Build Docker image

```bash
docker build -t lukaskellerstein/my-first-temporal-worker:latest .
```

### Step 3: Log in to Docker Hub

```bash
docker login
```

Enter your Docker Hub credentials.

### Step 4: Push image to Docker Hub

```bash
docker push lukaskellerstein/my-first-temporal-worker:latest
```

### Step 5: Update Kubernetes deployment

Edit `k8s/deployment.yaml` and update line 19 with your image:

```yaml
image: lukaskellerstein/my-first-temporal-worker:latest
```

### Step 6: Configure Temporal connection

The default configuration in `k8s/configmap.yaml` is already set correctly for workers running inside the cluster:

```yaml
TEMPORAL_HOST: "temporaltest-frontend.temporal.svc.cluster.local:7233"
```

This uses the internal Kubernetes service DNS name. No changes needed unless you have a different Temporal deployment.

## Part 2: Deploy to Kubernetes

### Step 1: Apply ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
```

### Step 2: Apply Deployment

```bash
kubectl apply -f k8s/deployment.yaml
```

### Step 3: Verify pods are running

```bash
kubectl get pods -l app=temporal-worker
```

Expected output:

```
NAME                              READY   STATUS    RESTARTS   AGE
temporal-worker-xxxxxxxxx-xxxxx   1/1     Running   0          30s
```

### Step 4: Check worker logs

```bash
kubectl logs -l app=temporal-worker -f
```

You should see:

```
INFO - Starting Temporal worker...
INFO - Successfully connected to Temporal server
INFO - Worker starting - ready to process workflows!
```

## Part 3: Start Workflows

### Step 1: Navigate to starter directory

```bash
cd MY/15_k8s/starter
```

### Step 2: Create virtual environment

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 3: Install dependencies

```bash
uv sync
```

### Step 4: Start a workflow

The default Temporal host is already configured as `192.168.5.65:30733` (Traefik NodePort).

No environment variables needed if using defaults:

```bash
python starter.py start 42
```

Or with custom workflow ID:

```bash
python starter.py start 42 my-workflow-1
```

If you need to override the Temporal host:

```bash
export TEMPORAL_HOST=192.168.5.65:30733
python starter.py start 42
```

### Step 5: Check workflow status

```bash
python starter.py status my-workflow-1
```

### Step 6: View in Temporal UI

Open: http://192.168.5.65:31666/temporal-web

## Common Operations

### Scale workers

```bash
kubectl scale deployment temporal-worker --replicas=5
```

### View worker logs

```bash
kubectl logs -l app=temporal-worker -f
```

### Restart workers

```bash
kubectl rollout restart deployment temporal-worker
```

### Delete deployment

```bash
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/configmap.yaml
```

### Update worker code

1. Make changes to `worker/worker.py`
2. Rebuild image: `docker build -t YOUR_DOCKERHUB_USERNAME/temporal-worker:latest .`
3. Push image: `docker push YOUR_DOCKERHUB_USERNAME/temporal-worker:latest`
4. Restart deployment: `kubectl rollout restart deployment temporal-worker`

## Troubleshooting

### Pods not starting

Check pod status:

```bash
kubectl describe pod -l app=temporal-worker
kubectl logs -l app=temporal-worker
```

### Image pull errors

Verify image exists on Docker Hub:

```bash
docker pull YOUR_DOCKERHUB_USERNAME/temporal-worker:latest
```

Make sure the image name in `k8s/deployment.yaml` matches.

### Worker can't connect to Temporal

Check `k8s/configmap.yaml` has correct `TEMPORAL_HOST`.

Test connectivity from a pod:

```bash
kubectl run test-pod --rm -it --image=busybox -- sh
# Inside pod:
nc -zv temporaltest-frontend.temporal.svc.cluster.local 7233
```

### Starter can't connect to Temporal

Test connectivity to the Traefik NodePort:

```bash
nc -zv 192.168.5.65 30733
# or
telnet 192.168.5.65 30733
```

Verify Traefik service is running:

```bash
kubectl get services -n traefik
# Should show port 7233:30733/TCP
```

### Workflows not being processed

Verify task queue names match:

- Worker: Check `k8s/configmap.yaml` → `TASK_QUEUE`
- Starter: Check environment variable or default in `starter.py`

## Environment Variables

### Worker (k8s/configmap.yaml)

| Variable             | Default                                                 | Description                        |
| -------------------- | ------------------------------------------------------- | ---------------------------------- |
| `TEMPORAL_HOST`      | `temporaltest-frontend.temporal.svc.cluster.local:7233` | Temporal server (internal cluster) |
| `TASK_QUEUE`         | `k8s-multiple-nodes-task-queue`                         | Task queue name                    |
| `TEMPORAL_NAMESPACE` | `default`                                               | Temporal namespace                 |

### Starter (environment or defaults)

| Variable             | Default                         | Description                        |
| -------------------- | ------------------------------- | ---------------------------------- |
| `TEMPORAL_HOST`      | `192.168.5.65:30733`            | Temporal server (Traefik NodePort) |
| `TASK_QUEUE`         | `k8s-multiple-nodes-task-queue` | Task queue name                    |
| `TEMPORAL_NAMESPACE` | `default`                       | Temporal namespace                 |

## What Gets Deployed

- **2 worker pods** (can be scaled)
- **ConfigMap** with Temporal connection settings
- **Deployment** managing worker lifecycle

Workers connect to Temporal and process workflows from the `k8s-multiple-nodes-task-queue` task queue.

## Architecture

```
┌──────────────────────────────────────────────────┐
│           Your Local Machine                     │
│                                                  │
│  starter/                                        │
│  └── starter.py  ← Triggers workflows            │
│         ↓                                        │
│    192.168.5.65:30733 (gRPC)                     │
└─────────┼────────────────────────────────────────┘
          ↓
    Traefik NodePort 30733
          ↓
┌─────────┴────────────────────────────────────────┐
│        Kubernetes Cluster                        │
│                                                  │
│  ┌───────────────────────────────────────┐      │
│  │  Traefik (namespace: traefik)         │      │
│  │  - NodePort 30733 → 7233 (gRPC)       │      │
│  │  - NodePort 31666 → 80 (HTTP)         │      │
│  └───────────────┬───────────────────────┘      │
│                  ↓                               │
│  ┌───────────────┴───────────────────────┐      │
│  │  Temporal (namespace: temporal)       │      │
│  │                                       │      │
│  │  temporaltest-frontend:7233           │      │
│  │  ↓                                    │      │
│  │  Task Queue                           │      │
│  │  ↓                                    │      │
│  └───────────────┬───────────────────────┘      │
│                  ↓                               │
│  ┌───────────────┴───────────────────────┐      │
│  │  Worker Pods (×2)                     │      │
│  │  └── worker.py  ← Process workflows   │      │
│  └───────────────────────────────────────┘      │
│                                                  │
└──────────────────────────────────────────────────┘
           ↓
    192.168.5.65:31666/temporal-web
           ↓
   View in browser
```

**Key Points**:

- **Workers** connect directly to Temporal frontend via internal cluster DNS: `temporaltest-frontend.temporal.svc.cluster.local:7233`
- **Starter** connects via Traefik NodePort: `192.168.5.65:30733` (gRPC)
- **Web UI** is accessible via Traefik NodePort: `http://192.168.5.65:31666/temporal-web` (HTTP)
- **Traefik** exposes both gRPC (30733) and HTTP (31666) on NodePorts
