# Helm Chart Documentation — DevOps Info Service

This document provides comprehensive documentation for the **devops-info-service** Helm chart, including chart structure, configuration, hooks, installation, and operational procedures.

---

## Table of Contents

1. [Chart Overview](#chart-overview)
2. [Chart Structure](#chart-structure)
3. [Configuration Guide](#configuration-guide)
4. [Hook Implementation](#hook-implementation)
5. [Installation Guide](#installation-guide)
6. [Operations](#operations)
7. [Testing & Validation](#testing--validation)
8. [Troubleshooting](#troubleshooting)

---

## Chart Overview

### About This Chart

The **devops-info-service** Helm chart packages a FastAPI-based information service for Kubernetes deployment. It provides a production-ready chart with:

- **Templated Kubernetes manifests** for reusable deployments
- **Environment-specific configurations** for dev, staging, and production
- **Helm hooks** for pre/post-install lifecycle management
- **Health checks** (liveness and readiness probes)
- **Rolling update strategy** with zero-downtime deployments
- **Pod security contexts** with non-root user execution
- **Resource limits and requests** for proper cluster management

### Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Environment Support** | Separate values files for dev and prod with different replicas, resources, and configurations |
| **Lifecycle Hooks** | Pre-install and post-install hooks for validation and smoke testing |
| **Health Management** | Configurable liveness and readiness probes |
| **Security** | Non-root pod execution, proper security contexts |
| **Rolling Updates** | Zero-downtime deployments with maxSurge and maxUnavailable settings |
| **Reusable Templates** | Helper templates for consistent naming and labeling |

### Chart Metadata

```yaml
apiVersion: v2
name: devops-info-service
description: Helm chart for DevOps Info Service - a FastAPI-based information service
type: application
version: 0.1.0
appVersion: "1.0"
```

---

## Chart Structure

### Directory Layout

```
devops-chart/
├── Chart.yaml                    # Chart metadata and version info
├── values.yaml                   # Default configuration values
├── values-dev.yaml              # Development environment overrides
├── values-prod.yaml             # Production environment overrides
├── templates/
│   ├── deployment.yaml          # Kubernetes Deployment template
│   ├── service.yaml             # Kubernetes Service template
│   ├── _helpers.tpl             # Template helper functions
│   └── hooks/
│       ├── pre-install-job.yaml # Pre-install hook for validation
│       └── post-install-job.yaml # Post-install hook for smoke tests
└── README.md                     # (Optional) Chart README
```

### Key Template Files

#### `templates/deployment.yaml`
- **Purpose:** Defines the Kubernetes Deployment for the DevOps Info Service
- **Templating:** Uses values for replica count, image, resources, probes
- **Features:**
  - Rolling update strategy
  - Health checks (liveness & readiness)
  - Resource limits and requests
  - Pod security context
  - Dynamic labeling via helpers

#### `templates/service.yaml`
- **Purpose:** Exposes the deployment as a Kubernetes Service
- **Templating:** Service type (NodePort/LoadBalancer) and port configuration
- **Features:**
  - Environment-aware service type (NodePort for dev, LoadBalancer for prod)
  - Port mapping (80 → 8080)
  - SessionAffinity configuration

#### `templates/_helpers.tpl`
- **Purpose:** Shared template functions for consistency
- **Functions:**
  - `devops-chart.name` - Generates chart name
  - `devops-chart.fullname` - Generates fully qualified release name
  - `devops-chart.chart` - Generates chart label
  - `devops-chart.labels` - Generates common labels
  - `devops-chart.selectorLabels` - Generates selector labels

#### `templates/hooks/pre-install-job.yaml`
- **Purpose:** Runs before chart installation
- **Use Case:** Validation, namespace checks, prerequisites
- **Hook Weight:** -5 (runs before main resources)
- **Deletion Policy:** hook-succeeded (deleted after successful execution)

#### `templates/hooks/post-install-job.yaml`
- **Purpose:** Runs after chart installation
- **Use Case:** Smoke tests, health verification, notifications
- **Hook Weight:** 5 (runs after main resources)
- **Deletion Policy:** hook-succeeded (deleted after successful execution)

### Values Organization Strategy

Values are organized hierarchically for clarity:

```yaml
replicaCount: 3              # Deployment scaling
image:                       # Container image settings
  repository: ...
  tag: ...
  pullPolicy: ...
service:                     # Service configuration
  type: NodePort
  port: ...
  targetPort: ...
resources:                   # Resource constraints
  limits: ...
  requests: ...
livenessProbe:              # Health check settings
readinessProbe:
securityContext:            # Security settings
strategy:                   # Deployment strategy
namespace:                  # K8s namespace
labels:                     # Custom labels
```

---

## Configuration Guide

### Default Values (values.yaml)

The default configuration is suitable for development/testing:

```yaml
replicaCount: 3                           # 3 replicas for basic HA

image:
  repository: poeticlama/devops-info-service
  tag: "1.0"
  pullPolicy: IfNotPresent               # Use cached images when possible

service:
  type: NodePort
  port: 80                               # External port
  targetPort: 8080                       # Container port
  nodePort: 30080                        # Fixed node port

resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi

livenessProbe:                           # Pod restart on failure
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 3

readinessProbe:                          # Traffic routing control
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 3
  failureThreshold: 2

securityContext:
  runAsNonRoot: true                    # Run as non-root user
  runAsUser: 1000
  fsGroup: 1000

strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1                         # 1 extra pod during update
    maxUnavailable: 0                   # Zero downtime

namespace: default
```

### Development Configuration (values-dev.yaml)

For development and testing environments:

```yaml
replicaCount: 1                         # Single replica for dev

image:
  tag: "latest"                         # Use latest for development
  pullPolicy: Always                    # Always pull latest image

service:
  type: NodePort                        # Local access only
  nodePort: 30080

resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi

livenessProbe:
  initialDelaySeconds: 5                # Faster probe for dev
  periodSeconds: 10                     # Less frequent checks
  failureThreshold: 5                   # More tolerant

readinessProbe:
  initialDelaySeconds: 5
  periodSeconds: 10
```

**Use Dev Values:**
```bash
helm install devops-dev ./devops-chart -f ./devops-chart/values-dev.yaml
```

### Production Configuration (values-prod.yaml)

For production deployments:

```yaml
replicaCount: 5                         # Higher availability

image:
  tag: "1.0"                           # Specific version, not latest
  pullPolicy: IfNotPresent             # Use cached when possible

service:
  type: LoadBalancer                   # External load balancer
  
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi

livenessProbe:
  initialDelaySeconds: 30               # More time to start
  periodSeconds: 5                      # Frequent health checks
  failureThreshold: 3                   # Strict failure handling

readinessProbe:
  initialDelaySeconds: 10
  periodSeconds: 3
  failureThreshold: 2
```

**Use Prod Values:**
```bash
helm install devops-prod ./devops-chart -f ./devops-chart/values-prod.yaml
```

### Customization Examples

**Override Single Value:**
```bash
helm install myrelease ./devops-chart --set replicaCount=5
```

**Override Multiple Values:**
```bash
helm install myrelease ./devops-chart \
  --set replicaCount=5 \
  --set image.tag="2.0" \
  --set resources.limits.cpu=1000m
```

**Custom Namespace:**
```bash
helm install myrelease ./devops-chart \
  --namespace production \
  --create-namespace
```

**Important Configuration Points:**

| Parameter | Dev Value | Prod Value | Why? |
|-----------|-----------|-----------|------|
| `replicaCount` | 1 | 5 | Production needs HA |
| `image.tag` | latest | 1.0 | Prod uses specific versions |
| `service.type` | NodePort | LoadBalancer | External access in prod |
| `resources.limits.cpu` | 100m | 500m | More resources for prod |
| `livenessProbe.initialDelaySeconds` | 5 | 30 | Prod needs more startup time |

---

## Hook Implementation

### Overview

This chart implements two Helm lifecycle hooks for deployment validation and verification:

### Pre-Install Hook

**File:** `templates/hooks/pre-install-job.yaml`

**Purpose:** Validates environment and prerequisites before installation

**Configuration:**
```yaml
metadata:
  annotations:
    "helm.sh/hook": pre-install          # Execute before installation
    "helm.sh/hook-weight": "-5"          # Run first (lowest weight)
    "helm.sh/hook-delete-policy": hook-succeeded  # Delete after success
```

**Execution:**
1. Runs BEFORE any chart resources are created
2. Weight -5 means it runs with highest priority
3. If it fails, installation stops
4. Job is automatically deleted upon successful completion

**What It Does:**
- Validates prerequisites
- Checks namespace availability
- Prints deployment information
- Performs pre-flight checks

**Example Output:**
```
=== Pre-install Hook Execution ===
Starting pre-installation validation...
Current timestamp: Tue Apr 02 14:30:45 UTC 2026
Release name: my-release
Chart name: devops-info-service
Namespace: default
Pre-installation validation completed successfully
```

### Post-Install Hook

**File:** `templates/hooks/post-install-job.yaml`

**Purpose:** Performs smoke tests and validation after installation

**Configuration:**
```yaml
metadata:
  annotations:
    "helm.sh/hook": post-install         # Execute after installation
    "helm.sh/hook-weight": "5"           # Run after main resources
    "helm.sh/hook-delete-policy": hook-succeeded  # Delete after success
```

**Execution:**
1. Runs AFTER all chart resources are created and ready
2. Weight 5 means it runs after main deployment (weight 0)
3. Does not block deployment if it fails
4. Job is automatically deleted upon successful completion

**What It Does:**
- Verifies service deployment
- Runs basic connectivity tests
- Validates application readiness
- Confirms configuration

**Example Output:**
```
=== Post-install Hook Execution ===
Starting post-installation smoke tests...
Timestamp: Tue Apr 02 14:30:50 UTC 2026
Smoke test: Verifying service deployment
Deployment name: my-release-devops-info-service
Post-installation smoke tests completed successfully
```

### Hook Execution Order

**Timeline:**
```
1. Pre-install hook (weight: -5)         ← Runs first
   ↓
2. Main resources (deployment, service)   ← Weight: 0 (default)
   ↓
3. Post-install hook (weight: 5)         ← Runs last
   ↓
4. Both hooks deleted (hook-succeeded)
```

### Hook Deletion Policy

**hook-succeeded:** Automatically deletes the hook Job after successful completion

Benefits:
- Keeps cluster clean
- No orphaned Jobs
- Easier to re-run installations
- Clear audit trail of successful hooks

### Real-World Hook Scenarios

**Pre-Install Hooks:**
- Database schema migrations
- Namespace and RBAC validation
- Configuration secret verification
- Dependency checks

**Post-Install Hooks:**
- Integration tests
- Health endpoint verification
- Smoke tests
- Deployment notifications

---

## Installation Guide

### Prerequisites

```bash
# 1. Kubernetes cluster running
kubectl cluster-info

# 2. Helm CLI installed (v3+)
helm version

# 3. Chart accessible
ls -la k8s/devops-chart/
```

### Basic Installation

**Install with default values:**
```bash
helm install devops-service ./devops-chart
```

**Check installation:**
```bash
helm list
helm status devops-service
kubectl get all
```

### Environment-Specific Installation

**Development Deployment:**
```bash
# Install with dev values (1 replica, minimal resources)
helm install devops-dev ./devops-chart \
  -f ./devops-chart/values-dev.yaml \
  --namespace dev-env \
  --create-namespace

# Verify
helm list -n dev-env
kubectl get pods -n dev-env
```

**Production Deployment:**
```bash
# Install with prod values (5 replicas, LoadBalancer)
helm install devops-prod ./devops-chart \
  -f ./devops-chart/values-prod.yaml \
  --namespace production \
  --create-namespace

# Verify
helm list -n production
kubectl get pods -n production
kubectl get svc -n production
```

### Staging Deployment with Custom Values

```bash
# Create custom values for staging
helm install devops-staging ./devops-chart \
  --set replicaCount=3 \
  --set image.tag="1.0-rc" \
  --set service.type=NodePort \
  --namespace staging \
  --create-namespace
```

### Verify Installation

```bash
# Check release
helm list

# Get release status
helm status devops-service

# View rendered values
helm get values devops-service

# View applied manifests
helm get manifest devops-service

# Check pods
kubectl get pods -l app.kubernetes.io/name=devops-info-service

# Check service
kubectl get svc devops-service-devops-info-service

# Check hook jobs
kubectl get jobs -l app.kubernetes.io/name=devops-info-service
```

---

## Operations

### Viewing Configuration

**View Current Values:**
```bash
helm get values devops-service
```

**View Current Manifest:**
```bash
helm get manifest devops-service | head -100
```

**View All Release Info:**
```bash
helm get all devops-service
```

### Upgrading a Release

**Upgrade to New Values:**
```bash
# Upgrade to prod values
helm upgrade devops-service ./devops-chart \
  -f ./devops-chart/values-prod.yaml
```

**Upgrade with Value Changes:**
```bash
# Increase replicas
helm upgrade devops-service ./devops-chart \
  --set replicaCount=10
```

**Upgrade with New Chart Version:**
```bash
# Assuming new chart version available
helm upgrade devops-service ./devops-chart
```

**Monitor Upgrade Progress:**
```bash
# Watch rolling update
kubectl rollout status deployment/devops-service-devops-info-service

# Watch pods
kubectl get pods -w -l app.kubernetes.io/name=devops-info-service
```

### Rolling Back

**Rollback to Previous Release:**
```bash
# Rollback immediately
helm rollback devops-service

# Rollback to specific revision
helm get history devops-service
helm rollback devops-service 2

# Verify rollback
helm history devops-service
helm status devops-service
```

### Uninstalling

**Delete Release:**
```bash
helm uninstall devops-service
```

**Uninstall and Keep History:**
```bash
# Release deleted but history kept (can rollback later)
helm uninstall devops-service --keep-history
```

**Verify Uninstallation:**
```bash
helm list
kubectl get all
```

### Scaling

**Scale Manually:**
```bash
# Using Helm
helm upgrade devops-service ./devops-chart --set replicaCount=5

# Or using kubectl
kubectl scale deployment devops-service-devops-info-service --replicas=5
```

### Port Forwarding (Development)

**Access Service Locally:**
```bash
# NodePort service
kubectl port-forward svc/devops-service-devops-info-service 8000:80

# Access at http://localhost:8000
curl http://localhost:8000/
curl http://localhost:8000/health
```

---

## Testing & Validation

### Pre-Installation Testing

**Lint Chart:**
```bash
helm lint ./devops-chart
```

**Expected Output:**
```
==> Linting ./devops-chart
[INFO] Chart.yaml: icon is missing
1 chart(s) linted, no errors
```

**Render Templates Locally:**
```bash
helm template devops-service ./devops-chart | head -50
```

**Verify with Specific Values:**
```bash
helm template devops-service ./devops-chart \
  -f ./devops-chart/values-prod.yaml
```

**Dry-Run Installation:**
```bash
helm install devops-service ./devops-chart \
  --dry-run \
  --debug

# With prod values
helm install devops-service ./devops-chart \
  -f ./devops-chart/values-prod.yaml \
  --dry-run \
  --debug
```

### Post-Installation Validation

**Check Deployment:**
```bash
kubectl get deployment
kubectl describe deployment devops-service-devops-info-service
```

**Check Pod Status:**
```bash
kubectl get pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

**Check Service:**
```bash
kubectl get svc
kubectl describe svc devops-service-devops-info-service
```

**Verify Hooks Executed:**
```bash
# Pre-install hook
kubectl get jobs
kubectl describe job devops-service-devops-info-service-pre-install
kubectl logs job/devops-service-devops-info-service-pre-install

# Post-install hook
kubectl describe job devops-service-devops-info-service-post-install
kubectl logs job/devops-service-devops-info-service-post-install
```

**Expected Hook Logs:**

Pre-install:
```
=== Pre-install Hook Execution ===
Starting pre-installation validation...
Current timestamp: Tue Apr 02 14:30:45 UTC 2026
Release name: devops-service
Chart name: devops-info-service
Namespace: default
Pre-installation validation completed successfully
```

Post-install:
```
=== Post-install Hook Execution ===
Starting post-installation smoke tests...
Timestamp: Tue Apr 02 14:30:50 UTC 2026
Smoke test: Verifying service deployment
Deployment name: devops-service-devops-info-service
Post-installation smoke tests completed successfully
```

### Application Accessibility

**Test Health Endpoint:**
```bash
# Port-forward to access
kubectl port-forward svc/devops-service-devops-info-service 8000:80 &

# Test health
curl http://localhost:8000/health

# Test main endpoint
curl http://localhost:8000/

# Stop port-forward
kill %1
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-02T14:30:50Z"
}
```

### Multi-Environment Testing

**Dev Environment Test:**
```bash
# Install dev
helm install devops-dev ./devops-chart \
  -f ./devops-chart/values-dev.yaml \
  -n dev --create-namespace

# Verify 1 pod running
kubectl get pods -n dev

# Verify service type
kubectl get svc -n dev

# Cleanup
helm uninstall devops-dev -n dev
```

**Prod Environment Test:**
```bash
# Install prod
helm install devops-prod ./devops-chart \
  -f ./devops-chart/values-prod.yaml \
  -n prod --create-namespace

# Verify 5 pods running
kubectl get pods -n prod

# Verify service type (LoadBalancer)
kubectl get svc -n prod

# Cleanup
helm uninstall devops-prod -n prod
```

---

## Troubleshooting

### Common Issues and Solutions

**Issue: Pods in CrashLoopBackOff**
```bash
# Check pod logs
kubectl logs <pod-name>

# Check probe settings
kubectl describe pod <pod-name> | grep -A 10 "Readiness\|Liveness"

# Solution: May need to adjust initialDelaySeconds in values
```

**Issue: Service Not Accessible**
```bash
# Check service exists
kubectl get svc

# Check endpoints
kubectl get endpoints

# Solution: Verify pods are ready (Ready column shows 1/1)
kubectl get pods
```

**Issue: Hook Didn't Execute**
```bash
# Check hook annotations
kubectl get jobs
helm get manifest devops-service | grep -A 5 "helm.sh/hook"

# Check job logs
kubectl logs job/<hook-job-name>

# Solution: Verify hook metadata and weights
```

**Issue: Image Pull Errors**
```bash
# Check image pull policy
kubectl describe pod <pod-name> | grep "Image\|Pull"

# Solution: Use pullPolicy: IfNotPresent and ensure image exists
```

**Issue: OOMKilled (Out of Memory)**
```bash
# Check resource limits
helm get values devops-service | grep -A 5 "resources"

# Check actual pod usage
kubectl top pods

# Solution: Increase memory limits in values
```

### Debug Commands

```bash
# Full pod information
kubectl describe pod <pod-name>

# Pod events
kubectl get events

# Check hook execution timeline
kubectl get jobs --sort-by=.metadata.creationTimestamp

# Validate chart syntax
helm lint ./devops-chart

# Test template rendering
helm template devops-service ./devops-chart --debug

# Check release history
helm history devops-service

# Rollback if needed
helm rollback devops-service
```

---

## Summary

This Helm chart provides a production-ready deployment for the DevOps Info Service with:

✅ **Proper Templating** - All values externalized and configurable
✅ **Multi-Environment Support** - Dev and prod-specific configurations
✅ **Lifecycle Hooks** - Pre/post-install validation and testing
✅ **Health Checks** - Liveness and readiness probes
✅ **Security** - Non-root execution and proper contexts
✅ **Best Practices** - Helper templates, consistent naming, resource limits

For more information, see:
- [Helm Official Documentation](https://helm.sh/docs/)
- [Chart Best Practices](https://helm.sh/docs/chart_best_practices/)
- Lab 10 assignment details for additional context

