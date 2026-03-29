# Kubernetes Deployment

## Quick Start

```bash
# Apply all resources
kubectl apply -k .

# Or apply individually
kubectl apply -f configmap.yaml
kubectl apply -f redis.yaml
kubectl apply -f deployment.yaml
kubectl apply -f monitoring.yaml
```

## Requirements

- Kubernetes 1.24+
- kubectl configured
- Ingress controller (nginx)

## Components

| Component | Description |
|-----------|-------------|
| `configmap.yaml` | Config and secrets |
| `redis.yaml` | Redis cache (1 replica) |
| `deployment.yaml` | AI Pipeline (2-10 replicas) |
| `monitoring.yaml` | Prometheus |
| `ingress.yaml` | HTTP routing |

## Scaling

HPA configured for 2-10 replicas based on CPU/memory.

```bash
# Check status
kubectl get pods -n ai-pipeline
kubectl get svc -n ai-pipeline
kubectl get hpa -n ai-pipeline
```

## Access

```bash
# Port forward
kubectl port-forward -n ai-pipeline svc/ai-pipeline-service 8080:80

# Or via ingress (add to /etc/hosts)
echo "127.0.0.1 ai-pipeline.local" >> /etc/hosts
```
