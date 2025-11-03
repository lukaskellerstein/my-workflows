# Prefect - K8s

Documentation: https://github.com/PrefectHQ/prefect-helm

```bash
helm repo add prefect https://prefecthq.github.io/prefect-helm
helm search repo prefect
```

## 0. Create a `prefect` k8s namespace

Create namespace

```bash
kubectl create namespace prefect
```

## 1. Prefect Server

Documentation:
https://docs.prefect.io/v3/advanced/server-helm#deploy-a-server-with-helm

https://github.com/PrefectHQ/prefect-helm/blob/main/charts/prefect-server

Install server

```bash
helm upgrade --install prefect-server prefect/prefect-server --namespace prefect -f values.yaml
```

Expose it via traefik

```bash
kubectl apply -f server-ingress.yaml
```

## 2. Create a Work pool

Documentation: https://docs.prefect.io/v3/how-to-guides/deployment_infra/manage-work-pools

Via Prefect UI (Server) - Ex. `http://192.168.5.65:31666/prefect-server/work-pools/create`

- Choose `Kubernetes`
- Name `MyFirstWorkPool`
- Labels

```json
{
  "CreatedBy": "Worker"
}
```

- Namespace `createdbyworker`

# 3. Prefect worker

Documentation: https://docs.prefect.io/v3/advanced/server-helm#deploy-a-worker-with-helm

https://github.com/PrefectHQ/prefect-helm/tree/main/charts/prefect-worker

Install worker

```bash
helm upgrade --install prefect-worker-release prefect/prefect-worker --namespace prefect -f values.yaml
```

# Terraform

https://registry.terraform.io/providers/PrefectHQ/prefect/latest/docs

# Notes

Helm remove

```bash
helm uninstall <release_name> --namespace <namespace_name>
```

# UI

UI: `http://192.168.5.65:31666/prefect-server`

API SWAGGER: `http://192.168.5.65:31666/prefect-server/api/docs`
