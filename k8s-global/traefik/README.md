## Installation

```bash
helm upgrade --install traefik traefik/traefik -n traefik --create-namespace -f values.yaml
```

## Exposed NodePorts

After installation, Traefik exposes the following NodePorts:

- **HTTP (web)**: 30080
- **HTTPS (websecure)**: 30443
- **Temporal gRPC**: 30733

To verify:
```bash
kubectl get svc -n traefik traefik -o jsonpath='{range .spec.ports[*]}{.name}{": "}{.nodePort}{"\n"}{end}'
```

## Important: NodePort Configuration

NodePorts must be configured **inside each port definition** under the `ports` section:

```yaml
ports:
  web:
    nodePort: 30080  # ✅ Correct
```

NOT under `service.nodePorts`:

```yaml
service:
  nodePorts:
    http: 30080  # ❌ Ignored by Traefik chart
```
