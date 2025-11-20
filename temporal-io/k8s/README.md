# Temporal - K8s

## 0. Create a `temporal` k8s namespace

Create namespace

```bash
kubectl create namespace temporal
```

## 1. Install

```bash
helm upgrade --install \
    --repo https://go.temporal.io/helm-charts \
    -f values.yaml \
    temporaltest temporal \
    --timeout 15m \
    --namespace temporal
```

## 2. Expose web, frontend

### Apply Traefik ingress routes

```bash
kubectl apply -f ui-ingress.yaml
```

### Configure Traefik TCP entrypoint for gRPC (port 7233)

The gRPC endpoint is exposed via Traefik TCP routing. The configuration has been added to:

- `/home/lukas/Projects/Github/lukaskellerstein/my-workflows/k8s-global/traefik/values.yaml`

The TCP entrypoint `temporal-grpc` routes traffic to the Temporal frontend service on port 7233.

To verify the gRPC endpoint is working:

```bash
kubectl exec -n temporal deployment/temporaltest-admintools -- tctl --address <your-node-ip>:<grpc-nodeport> cluster health
```

Check the actual NodePort assigned:

```bash
kubectl get svc -n traefik traefik -o jsonpath='{.spec.ports[?(@.name=="temporal-grpc")].nodePort}'
```

## 3. Create default namespace

Create the default namespace for workflows:

```bash
kubectl exec -n temporal deployment/temporaltest-admintools -- tctl --namespace default namespace register
```

Verify it was created:

```bash
kubectl exec -n temporal deployment/temporaltest-admintools -- tctl --namespace default namespace describe
```

# Notes

## Upgrade existing deployment

```bash
helm upgrade \
    --repo https://go.temporal.io/helm-charts \
    -f values.yaml \
    temporaltest temporal \
    --timeout 15m \
    --namespace temporal
```

## Remove deployment

```bash
helm uninstall temporaltest --namespace temporal
```

## Access endpoints

After deployment, access Temporal services at:

- **Web UI**: `http://192.168.5.65:30080/temporal-web`
- **Frontend HTTP API**: `http://192.168.5.65:30080/temporal-frontend`
- **gRPC (via Traefik)**: `192.168.5.65:30733`

To verify the ports:

```bash
kubectl get svc -n traefik traefik -o jsonpath='{range .spec.ports[*]}{.name}{": "}{.nodePort}{"\n"}{end}'
```
