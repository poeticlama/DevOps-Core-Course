# StatefulSet & Persistent Storage Implementation

## Overview

This document outlines the implementation of StatefulSets for the DevOps Info Service, providing stable network identities and persistent per-pod storage for the visits counter.

### Why StatefulSet?

The DevOps Info Service maintains a visits counter stored on persistent storage. StatefulSets are used instead of Deployments because they provide:

1. **Stable, Unique Network Identifiers** - Each pod has a stable DNS name (e.g., `devops-info-service-0`, `devops-info-service-1`)
2. **Stable, Persistent Storage** - Each pod gets its own PVC that persists across pod restarts
3. **Ordered Deployment/Scaling** - Pods are created and terminated in a predictable order

### StatefulSet vs Deployment

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod Names | Random suffix (e.g., `abc123def456`) | Ordered index (pod-0, pod-1, pod-2) |
| Storage | Shared PVC or ephemeral | Per-pod PVC via volumeClaimTemplates |
| Scaling | Any order | Ordered (0→1→2) |
| Network ID | Random, dynamically assigned | Stable DNS name |
| Use Case | Stateless applications | Stateful applications (databases, message queues) |

## Implementation Details

### 1. StatefulSet Configuration

**File:** `devops-chart/templates/statefulset.yaml`

Key features:
- `serviceName`: Points to the headless service for DNS resolution
- `volumeClaimTemplates`: Automatically creates one PVC per pod
- Each pod receives a stable hostname based on its ordinal index (0, 1, 2, ...)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: devops-info-service
spec:
  serviceName: devops-info-service-headless
  replicas: 3
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: [ "ReadWriteOnce" ]
        resources:
          requests:
            storage: 1Gi
```

### 2. Headless Service

**File:** `devops-chart/templates/headless-service.yaml`

A headless service has `clusterIP: None`, which:
- Does not assign a single cluster IP to the service
- Instead, creates DNS records for each pod
- Allows direct pod-to-pod communication

DNS names are in the format:
```
<pod-name>.<service-name>.<namespace>.svc.cluster.local
```

Example:
- `devops-info-service-0.devops-info-service-headless.default.svc.cluster.local`
- `devops-info-service-1.devops-info-service-headless.default.svc.cluster.local`
- `devops-info-service-2.devops-info-service-headless.default.svc.cluster.local`

### 3. PersistentVolumeClaims

VolumeClaimTemplates automatically generate:
- One PVC per pod replica
- Each with a stable name: `data-<pod-name>`
- Each pod mounts its own PVC to `/data`
- Data persists even if a pod is deleted and recreated

## Verification Steps

### Check StatefulSet Resources

```bash
# View the StatefulSet
kubectl get statefulset
kubectl describe statefulset devops-info-service

# View pods with their ordinal names
kubectl get pods

# View PersistentVolumeClaims
kubectl get pvc

# View headless service
kubectl get svc | grep headless
```

### Test DNS Resolution

```bash
# Exec into the first pod
kubectl exec -it devops-info-service-0 -- /bin/sh

# Inside the pod, test DNS resolution to other pods
nslookup devops-info-service-1.devops-info-service-headless
nslookup devops-info-service-2.devops-info-service-headless

# Verify the IP addresses are different for each pod
```

### Test Per-Pod Storage Isolation

Each pod maintains its own visit counter. The visits counter is stored in `/data/visits` file.

```bash
# Check visits count in pod 0
kubectl exec devops-info-service-0 -- cat /data/visits

# Check visits count in pod 1
kubectl exec devops-info-service-1 -- cat /data/visits

# Check visits count in pod 2
kubectl exec devops-info-service-2 -- cat /data/visits
```

Each pod will have different visit counts because they maintain separate `/data` mounts.

### Port-Forward to Access Individual Pods

```bash
# In separate terminals, port-forward to each pod
kubectl port-forward pod/devops-info-service-0 8080:8000 &
kubectl port-forward pod/devops-info-service-1 8081:8000 &
kubectl port-forward pod/devops-info-service-2 8082:8000 &

# Make requests to each pod's visit endpoint
curl http://localhost:8080/visits
curl http://localhost:8081/visits
curl http://localhost:8082/visits

# Each pod will show different visit counts
# Pod 0: {"visits": 5}
# Pod 1: {"visits": 3}
# Pod 2: {"visits": 7}
```

### Test Persistence

The key feature of StatefulSets is that data persists when a pod is deleted:

```bash
# Record the current visit count for pod-0
kubectl exec devops-info-service-0 -- cat /data/visits
# Output: 42

# Delete the pod (not the StatefulSet)
kubectl delete pod devops-info-service-0

# The StatefulSet controller will automatically restart it with the same name
# Wait for pod to be ready
kubectl get pod devops-info-service-0

# Check that the visit count is preserved
kubectl exec devops-info-service-0 -- cat /data/visits
# Output: 42 (same as before)

# The PVC persisted the data even though the pod was deleted
```

## Pod Identity & Network Characteristics

### Stable Hostname

Each pod's hostname is derived from its ordinal index:

```bash
# Inside pod-0
kubectl exec devops-info-service-0 -- hostname
# Output: devops-info-service-0

# Inside pod-1
kubectl exec devops-info-service-1 -- hostname
# Output: devops-info-service-1
```

### Pod Ordering

When scaling, pods are created in order (0→1→2) and terminated in reverse order (2→1→0):

```bash
# Scale up from 3 to 5 replicas
kubectl scale statefulset devops-info-service --replicas=5

# Pods 0-3 exist first, then 4 and 5 are created in sequence

# Scale down to 2
kubectl scale statefulset devops-info-service --replicas=2

# Pods 2 and 3 are deleted first, leaving 0 and 1
```

### Storage Affinity

Pods always mount the same PVC, even after restarts:
- Pod-0 always mounts `data-devops-info-service-0`
- Pod-1 always mounts `data-devops-info-service-1`
- Pod-2 always mounts `data-devops-info-service-2`

## Configuration in Helm

### values.yaml Settings

```yaml
# Persistence configuration for visits counter
persistence:
  enabled: true
  size: 1Gi
  storageClass: null  # Use default storage class if null
```

These values are used in the StatefulSet's `volumeClaimTemplates` section.

## Deployment Instructions

### Deploy with Helm

```bash
# From the app_python directory
helm install devops-info-service ./k8s/devops-chart

# Or upgrade if already installed
helm upgrade devops-info-service ./k8s/devops-chart
```

### Verify Deployment

```bash
# Check all resources
kubectl get all -l app.kubernetes.io/instance=devops-info-service

# Expected output should show:
# - 1 StatefulSet (devops-info-service)
# - 3 Pods (devops-info-service-0, -1, -2)
# - 2 Services (devops-info-service for external access, devops-info-service-headless for DNS)
# - 3 PVCs (data-devops-info-service-0, -1, -2)
```

## Differences from Previous Lab 12 Deployment

**Lab 12 (Deployment):**
- Used a shared PVC for all replicas
- All pods incremented the same visit counter
- No stable per-pod storage

**Lab 15 (StatefulSet):**
- Each pod has its own PVC via volumeClaimTemplates
- Each pod maintains its own visit counter
- Per-pod storage isolation with stable identities
- Data persists across pod failures and restarts

## When to Use StatefulSets

Use StatefulSets for:
- **Databases** (MySQL, PostgreSQL, MongoDB) - need stable identities and persistent storage
- **Message Queues** (Kafka, RabbitMQ) - need per-broker storage and stable identities
- **Distributed Systems** (Elasticsearch, Cassandra) - need stable node identities
- **Applications requiring stable hostnames** - DNS must resolve to the same pod

Use Deployments for:
- **Stateless applications** - web servers, APIs, microservices
- **Applications that don't need per-pod storage** - can share storage or use ephemeral
- **Applications where pod identity doesn't matter** - can be replaced with new pods

## Summary

StatefulSets provide critical guarantees for stateful applications:
1. **Stable Network Identity** - pods always have the same DNS name
2. **Persistent Storage** - each pod gets dedicated storage that persists
3. **Ordered Operations** - predictable scaling and termination

The DevOps Info Service now uses StatefulSets to maintain per-pod visit counters with data that persists across pod restarts and failures.

