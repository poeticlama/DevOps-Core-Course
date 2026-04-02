# Kubernetes Deployment — DevOps Info Service

## Quick Start

### Prerequisites
- kubectl installed
- kind or minikube cluster running
- Docker image: `poeticlama/devops-info-service:1.0`

### Deploy

```bash
# Create namespace (optional)
kubectl create namespace devops

# Apply manifests
kubectl apply -f deployment.yml -n devops
kubectl apply -f service.yml -n devops

# Verify deployment
kubectl get all -n devops
```

---

## Architecture Overview

### Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│         Kubernetes Cluster (kind)               │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │  Service: devops-info-service (NodePort)    │
│  │  Port: 80 → Container: 8080 (NodePort: 30080) │
│  └────────────────┬────────────────────────┘   │
│                   │                            │
│        ┌──────────┼──────────┐                │
│        │          │          │                │
│  ┌─────▼──┐ ┌────▼───┐ ┌───▼────┐            │
│  │ Pod 1  │ │ Pod 2  │ │ Pod 3  │            │
│  │ 8080   │ │ 8080   │ │ 8080   │            │
│  │ (1/1)  │ │ (1/1)  │ │ (1/1)  │            │
│  └────────┘ └────────┘ └────────┘            │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Resource Summary

| Resource | Count | Details |
|----------|-------|---------|
| **Pods** | 3 | Running replicas of app |
| **Service** | 1 | NodePort exposing port 30080 |
| **Deployment** | 1 | Manages Pod replicas |

### Network Flow

1. External request → Node IP:30080
2. NodePort Service → Load balanced across Pods
3. Pod receives request on port 8080
4. FastAPI application processes request
5. Response returned through same path

---

## Manifest Files

### deployment.yml

**Purpose**: Defines how the application should run in Kubernetes

**Key Configuration:**

```yaml
replicas: 3                    # High availability
strategy:
  type: RollingUpdate          # Gradual updates
  rollingUpdate:
    maxUnavailable: 0          # Zero downtime
    maxSurge: 1                # Extra pod during update

resources:
  requests:                    # Minimum guaranteed
    memory: "128Mi"
    cpu: "100m"
  limits:                      # Maximum allowed
    memory: "256Mi"
    cpu: "200m"

livenessProbe:                 # Restart if unhealthy
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:                # Remove from load balancer if not ready
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5

securityContext:               # Production security
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL
```

**Why these values?**

- **3 Replicas**: Provides high availability and load distribution
- **Zero downtime strategy**: Ensures service continuity during updates
- **Resource requests**: Guarantees minimum performance and enables proper scheduling
- **Resource limits**: Prevents resource starvation and protects cluster
- **Health checks**: Ensures Pods are healthy and ready for traffic
- **Security context**: Implements principle of least privilege

### service.yml

**Purpose**: Exposes Pods to external traffic

**Configuration:**

```yaml
type: NodePort                 # External access on static port
selector:
  app: devops-info-service     # Route to pods with this label

ports:
  - port: 80                   # Service port
    targetPort: 8080           # Container port
    nodePort: 30080            # External access port (30000-32767)
```

**Routing Flow:**
```
External Client
    ↓
NodePort 30080
    ↓
Service port 80
    ↓
Pod port 8080
```

---

## Health Checks Implementation

### Liveness Probe

**Endpoint**: `GET /health`

**Purpose**: Restart container if application becomes unhealthy

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-02T10:17:20.123Z",
  "uptime_seconds": 150
}
```

**Configuration Rationale**:
- `initialDelaySeconds: 10` — Allow app startup before checking
- `periodSeconds: 10` — Regular intervals to catch failures
- `failureThreshold: 3` — Tolerate temporary failures

---

### Readiness Probe

**Endpoint**: `GET /health`

**Purpose**: Remove Pod from load balancing if not ready to serve traffic

**Configuration Rationale**:
- `initialDelaySeconds: 5` — Faster detection of readiness
- `periodSeconds: 5` — More frequent checks for quick responsiveness
- `failureThreshold: 2` — Quicker removal if issues detected

---

## Operations

### Deployment Commands

```bash
# Apply manifests
kubectl apply -f deployment.yml
kubectl apply -f service.yml

# View resources
kubectl get deployments
kubectl get pods
kubectl get services

# Get detailed information
kubectl describe deployment devops-info-service
kubectl describe pod <pod-name>
kubectl describe service devops-info-service

# View logs
kubectl logs <pod-name>
kubectl logs <pod-name> --follow

# Execute command in Pod
kubectl exec <pod-name> -- curl http://localhost:8080/health
```

---

### Scaling Operations

**Scale to 5 replicas**:
```bash
# Option 1: Edit manifest
# Change replicas: 3 to replicas: 5
kubectl apply -f deployment.yml

# Option 2: Imperative scaling
kubectl scale deployment devops-info-service --replicas=5

# Monitor progress
kubectl get pods -w
```

**Output**:
```
devops-info-service-5d8b9f8f9-2pxkw       1/1     Running   0          45s
devops-info-service-5d8b9f8f9-7qr9j       1/1     Running   0          45s
devops-info-service-5d8b9f8f9-wvklm       1/1     Running   0          45s
devops-info-service-5d8b9f8f9-4zxpq       1/1     Running   0          15s
devops-info-service-5d8b9f8f9-8mnop       1/1     Running   0          10s
```

---

### Rolling Updates

**Update image version**:

1. Edit `deployment.yml`:
```yaml
containers:
- name: devops-info-service
  image: poeticlama/devops-info-service:1.1  # New version
```

2. Apply manifest:
```bash
kubectl apply -f deployment.yml
```

3. Monitor rollout:
```bash
kubectl rollout status deployment/devops-info-service
kubectl get pods -w
```

**How it works**:
- Launches new Pod with updated image
- Waits for readiness probe to pass
- Routes traffic to new Pod
- Terminates old Pod gracefully
- Repeats for each Pod (with maxSurge/maxUnavailable rules)

**Zero Downtime**: `maxUnavailable: 0` ensures minimum 3 replicas always available

---

### Rollback Operations

**View rollout history**:
```bash
kubectl rollout history deployment/devops-info-service
```

**Rollback to previous version**:
```bash
kubectl rollout undo deployment/devops-info-service
```

**Rollback to specific revision**:
```bash
kubectl rollout undo deployment/devops-info-service --to-revision=1
```

---

## Service Access

### Using kubectl port-forward

```bash
kubectl port-forward service/devops-info-service 8080:80
```

Then access: `http://localhost:8080`

### Direct NodePort Access (kind)

```bash
# Get kind node IP
kubectl get nodes -o wide

# Access via NodePort
curl http://<node-ip>:30080/
```

### Testing Endpoints

```bash
# Root endpoint (main service info)
curl http://localhost:8080/

# Health check
curl http://localhost:8080/health

# Prometheus metrics
curl http://localhost:8080/metrics
```

---

## Monitoring

### View Pod Metrics

```bash
# Check resource usage
kubectl top pods
kubectl top nodes
```

**Example output**:
```
NAME                                       CPU(cores)   MEMORY(bytes)
devops-info-service-5d8b9f8f9-2pxkw       45m          95Mi
devops-info-service-5d8b9f8f9-7qr9j       42m          92Mi
devops-info-service-5d8b9f8f9-wvklm       48m          98Mi
```

### View Application Logs

```bash
# Single pod
kubectl logs devops-info-service-5d8b9f8f9-2pxkw

# Follow logs
kubectl logs -f devops-info-service-5d8b9f8f9-2pxkw

# All pods in deployment
kubectl logs -l app=devops-info-service
```

### Prometheus Metrics

Access via `/metrics` endpoint:

```bash
curl http://localhost:8080/metrics
```

**Key metrics**:
- `http_requests_total` — Total requests per endpoint
- `http_request_duration_seconds` — Request latency histogram
- `http_requests_in_progress` — Currently processing requests
- `devops_info_system_collection_seconds` — System info collection time

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods

# Get detailed error
kubectl describe pod <pod-name>

# Check logs for errors
kubectl logs <pod-name>

# Common issues:
# - Image pull error: Verify image exists and access
# - Readiness probe failed: Check if /health endpoint returns 200
# - Insufficient resources: Check node capacity
```

### Service Not Reachable

```bash
# Verify service exists and has endpoints
kubectl get service devops-info-service
kubectl get endpoints devops-info-service

# Test connectivity to pod directly
kubectl port-forward pod/<pod-name> 8080:8080
curl http://localhost:8080/

# Check service selector matches pod labels
kubectl get pods --show-labels
```

### High Resource Usage

```bash
# Check current usage
kubectl top pods
kubectl top nodes

# Identify resource-hungry pods
kubectl top pods --sort-by=memory

# Adjust limits in deployment.yml if needed
# Monitor trends over time
```

---

## Production Considerations

### Configuration Management

**Current**: Environment variables in deployment manifest

**Production Improvement**: Use ConfigMaps

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: "INFO"
---
spec:
  containers:
  - envFrom:
    - configMapRef:
        name: app-config
```

**Benefit**: Change configuration without redeploying

---

### Secrets Management

For sensitive data (API keys, credentials):

```bash
kubectl create secret generic app-secrets \
  --from-literal=api-key=secret-value
```

```yaml
env:
- name: API_KEY
  valueFrom:
    secretKeyRef:
      name: app-secrets
      key: api-key
```

---

### Persistence

For stateful data:

```yaml
volumeClaimTemplates:
- metadata:
    name: data
  spec:
    accessModes: ["ReadWriteOnce"]
    resources:
      requests:
        storage: 10Gi
```

**Note**: Current application is stateless, not needed.

---

### High Availability

For multi-zone setup:

```yaml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - devops-info-service
        topologyKey: kubernetes.io/hostname
```

**Effect**: Spread Pods across different nodes

---

### Observability Strategy

1. **Metrics**: Prometheus scraping `/metrics` endpoint
2. **Logs**: JSON format to stdout, collected by log aggregator
3. **Tracing**: Implement distributed tracing for request flows
4. **Alerting**: Rule-based alerts on error rates, resource usage

---

## Resource Requirements Summary

| Resource | Value | Justification |
|----------|-------|---------------|
| **Memory Request** | 128Mi | Lightweight FastAPI app |
| **Memory Limit** | 256Mi | Prevent OOM, 2x request |
| **CPU Request** | 100m | I/O bound workload |
| **CPU Limit** | 200m | 2x request for bursts |
| **Replicas** | 3 | High availability |
| **Readiness Delay** | 5s | Quick startup |
| **Liveness Delay** | 10s | Allow initialization |

---

## Manifest Validation

Validate YAML syntax:

```bash
kubectl apply -f deployment.yml --dry-run=client
kubectl apply -f service.yml --dry-run=client
```

Check applied configuration:

```bash
kubectl get deployment devops-info-service -o yaml
kubectl get service devops-info-service -o yaml
```

---

## Cleanup

**Delete deployment and service**:

```bash
kubectl delete -f deployment.yml
kubectl delete -f service.yml

# Or delete all at once
kubectl delete -f .

# Verify cleanup
kubectl get all
```

---

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/quick-reference/)
- [Deployment Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Health Checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)

---

**Status**: ✅ Production Ready  
**Last Updated**: April 2, 2026  
**Kubernetes Version**: 1.33.0

