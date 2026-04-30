# ArgoCD GitOps Deployment Documentation

## Overview

This document provides a comprehensive guide to the ArgoCD GitOps implementation for the DevOps Info Service application. ArgoCD enables declarative, version-controlled Kubernetes deployments with automatic synchronization and self-healing capabilities.

---

## Task 1: ArgoCD Installation & Setup

### Installation Commands

1. **Add ArgoCD Helm Repository**
   ```bash
   helm repo add argo https://argoproj.github.io/argo-helm
   helm repo update
   ```

2. **Create Namespace and Install ArgoCD**
   ```bash
   kubectl create namespace argocd
   helm install argocd argo/argo-cd --namespace argocd
   ```

3. **Wait for All Components to Be Ready**
   ```bash
   kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s
   ```

### ArgoCD Components Deployed

- **argocd-server**: Web UI and API server
- **argocd-repo-server**: Git repository server
- **argocd-controller-manager**: Core ArgoCD controller
- **redis**: Caching layer
- **argocd-dex-server**: Authentication server

### Accessing the ArgoCD UI

1. **Port Forwarding Setup**
   ```bash
   kubectl port-forward svc/argocd-server -n argocd 8080:443
   ```

2. **Retrieve Initial Admin Password**
   ```bash
   kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
   ```

3. **Access the Web Interface**
   - URL: `https://localhost:8080`
   - Username: `admin`
   - Password: [Retrieved from above command]

### ArgoCD CLI Installation & Configuration

1. **CLI Installation**
   - macOS: `brew install argocd`
   - Linux: Download from [ArgoCD GitHub Releases](https://github.com/argoproj/argo-cd/releases)
   - Windows: Download from GitHub releases or use `choco install argocd-cli`

2. **Login to ArgoCD via CLI**
   ```bash
   argocd login localhost:8080 --insecure
   # Use admin username and password from above
   ```

3. **Verify Connection**
   ```bash
   argocd cluster list
   argocd repo list
   ```

---

## Task 2: Application Deployment

### Application Manifest Structure

#### Primary Application (`application.yaml`)

**Purpose**: Initial deployment with manual sync policy

**Configuration**:
- **Source Repository**: `https://github.com/poeticlama/DevOps-Core-Course.git`
- **Target Revision**: `main` branch
- **Helm Chart Path**: `app_python/k8s/devops-chart`
- **Values File**: `values.yaml`
- **Destination Namespace**: `default`
- **Sync Policy**: Manual (requires explicit sync trigger)

**Key Fields**:
- `repoURL`: Points to the GitHub repository containing the Helm chart
- `targetRevision`: Branch to track (main)
- `path`: Path to Helm chart within repository
- `helm.valueFiles`: Specifies which values file to use
- `destination.server`: Target Kubernetes API server
- `destination.namespace`: Where to deploy the application
- `syncPolicy.syncOptions`: Options like `CreateNamespace=true`

### Deployment Workflow

1. **Create ArgoCD Namespace**
   ```bash
   kubectl create namespace argocd
   ```

2. **Apply Application Manifest**
   ```bash
   kubectl apply -f app_python/k8s/argocd/application.yaml
   ```

3. **Observe in ArgoCD UI**
   - Application appears with "OutOfSync" status (no sync yet)
   - Shows difference between Git state and cluster state

4. **Trigger Manual Sync**
   
   Via UI:
   - Navigate to the application
   - Click "SYNC" button
   - Confirm sync operation

   Via CLI:
   ```bash
   argocd app sync python-app
   ```

5. **Verify Deployment**
   ```bash
   kubectl get pods -n default -l app.kubernetes.io/name=devops-info-service
   kubectl get svc -n default
   ```

### Sync Status Indicators

- **Synced**: Cluster state matches Git repository
- **OutOfSync**: Git has changes not yet applied to cluster
- **Unknown**: Unable to determine state (connection issues, etc.)
- **Syncing**: Synchronization in progress
- **Error**: Sync failed with errors

### Health Status Indicators

- **Healthy**: All resources healthy, application operational
- **Degraded**: Some resources unhealthy or failed
- **Progressing**: Resources still being deployed
- **Unknown**: Health status cannot be determined

### Testing GitOps Workflow

1. **Make a Change to Helm Chart**
   ```bash
   # Edit values.yaml - change replica count
   replicaCount: 5
   ```

2. **Commit and Push to Repository**
   ```bash
   git add app_python/k8s/devops-chart/values.yaml
   git commit -m "Update replica count for testing"
   git push origin main
   ```

3. **Observe ArgoCD Detecting Drift**
   - ArgoCD polls Git every 3 minutes
   - Application status changes to "OutOfSync"
   - ArgoCD UI shows the differences

4. **Manually Trigger Sync**
   ```bash
   argocd app sync python-app
   ```

5. **Verify Changes Applied**
   ```bash
   kubectl get pods -n default
   ```

---

## Task 3: Multi-Environment Deployment

### Environment Strategy

The application is deployed to multiple environments with different configurations:

| Environment | Namespace | Replicas | Image Tag | Sync Policy | Service Type | Use Case |
|-------------|-----------|----------|-----------|-------------|--------------|----------|
| Dev | `dev` | 1 | `latest` | Auto-sync | NodePort | Development & Testing |
| Prod | `prod` | 5 | `1.0` | Manual | LoadBalancer | Production |

### Namespace Creation

```bash
kubectl create namespace dev
kubectl create namespace prod
```

### Dev Application Configuration

**File**: `application-dev.yaml`

**Key Features**:
- **Auto-Sync Enabled**: Automatically applies Git changes
- **Self-Healing**: Reverts manual cluster changes
- **Prune Enabled**: Removes resources deleted from Git
- **Single Replica**: Lower resource consumption for development
- **Latest Image Tag**: Gets newest builds immediately
- **Lower Resource Limits**: Relaxed for development environment
- **Development Probes**: More lenient health checks

**Values File** (`values-dev.yaml`):
```yaml
replicaCount: 1
image:
  tag: "latest"
  pullPolicy: Always
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
```

**Sync Policy**:
```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
  syncOptions:
    - CreateNamespace=true
```

### Prod Application Configuration

**File**: `application-prod.yaml`

**Key Features**:
- **Manual Sync**: Requires explicit approval for deployments
- **No Self-Healing**: Prevents unexpected changes
- **No Pruning**: Requires explicit deletion confirmation
- **High Replicas**: Ensures availability and redundancy
- **Specific Image Tag**: Stable version, no auto-updates
- **High Resource Limits**: Ensures performance under load
- **Strict Health Checks**: Ensures application stability

**Values File** (`values-prod.yaml`):
```yaml
replicaCount: 5
image:
  tag: "1.0"
  pullPolicy: IfNotPresent
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi
service:
  type: LoadBalancer
```

**Sync Policy**:
```yaml
syncPolicy:
  syncOptions:
    - CreateNamespace=true
```

### Deployment Workflow for Each Environment

1. **Apply Dev Application**
   ```bash
   kubectl apply -f app_python/k8s/argocd/application-dev.yaml
   ```
   - Automatically syncs and maintains sync status
   - Watches for Git changes and applies automatically

2. **Apply Prod Application**
   ```bash
   kubectl apply -f app_python/k8s/argocd/application-prod.yaml
   ```
   - Remains OutOfSync until manually synced
   - Requires explicit approval for deployments

3. **Verify Both Environments**
   ```bash
   # List all applications
   argocd app list
   
   # Check dev environment
   kubectl get pods -n dev
   argocd app get python-app-dev
   
   # Check prod environment
   kubectl get pods -n prod
   argocd app get python-app-prod
   ```

### Why Manual Sync for Production?

1. **Change Review**: Deploy team reviews changes before production
2. **Controlled Release Timing**: Choose when to deploy (business hours, maintenance windows)
3. **Compliance Requirements**: Some standards require explicit deployment approval
4. **Rollback Planning**: Time to prepare for potential issues
5. **Reduced Risk**: Prevents automatic deployments of untested changes

### Multi-Environment Benefits

- **Isolation**: Each environment is independent
- **Configuration Management**: Different values per environment
- **Resource Optimization**: Dev uses fewer resources than prod
- **Release Strategy**: Dev auto-updates, prod controlled
- **Testing Ground**: Dev environment for validation before prod

---

## Task 4: Self-Healing & Sync Policies

### Understanding Self-Healing

**ArgoCD Self-Healing** (Configuration Drift Detection):
- Detects when cluster resources differ from Git
- Automatically reverts manual changes to match Git
- Requires `selfHeal: true` in sync policy

**Kubernetes Self-Healing** (Pod Replica Management):
- Kubernetes ReplicaSet/Deployment ensures desired pod count
- Automatically recreates failed pods
- Rebuilds nodes when needed

### Test 1: Manual Scale Detection & Auto-Revert

**Objective**: Test ArgoCD detecting and reverting manual scaling

**Setup**: Deploy application with `selfHeal: true` (dev environment)

**Test Procedure**:

1. **Baseline Check** (Time: 00:00)
   ```bash
   kubectl get deployment python-app-dev -n dev -o jsonpath='{.spec.replicas}'
   # Expected: 1
   ```

2. **Manual Scale Up** (Time: 00:00)
   ```bash
   kubectl scale deployment python-app-dev -n dev --replicas=5
   kubectl get pods -n dev
   # Should show 5 pods
   ```

3. **ArgoCD Detects Drift** (Time: 01:30)
   - ArgoCD polls Git every 3 minutes
   - Observes 5 pods running vs 1 in Git
   - Marks application as "OutOfSync"
   
   Check status:
   ```bash
   argocd app get python-app-dev
   # Status: OutOfSync
   ```

4. **View Drift Details**
   ```bash
   argocd app diff python-app-dev
   # Shows: spec.replicas: 1 (desired from Git)
   ```

5. **Self-Healing Reverts** (Time: 03:00)
   - ArgoCD's self-heal feature automatically runs sync
   - Scales deployment back to 1 replica
   
   Observe:
   ```bash
   kubectl get pods -n dev -w
   # Watch as pods are terminated
   kubectl get deployment python-app-dev -n dev -o jsonpath='{.spec.replicas}'
   # Back to: 1
   ```

**Evidence**:
- Manual scale: 5 replicas
- ArgoCD detection: 3 minutes
- Auto-revert: 3 minutes
- Final state: 1 replica (matches Git)

### Test 2: Pod Deletion (Kubernetes vs ArgoCD)

**Objective**: Understand pod recreation (Kubernetes) vs configuration sync (ArgoCD)

**Test Procedure**:

1. **Get Running Pod**
   ```bash
   kubectl get pods -n dev -l app.kubernetes.io/name=devops-info-service
   kubectl delete pod <pod-name> -n dev
   ```

2. **Immediate Recreation** (Time: <5s)
   - Kubernetes Deployment controller immediately creates new pod
   - **This is NOT ArgoCD, it's Kubernetes**
   - ReplicaSet ensures desired pod count is always maintained
   
   ```bash
   kubectl get pods -n dev -w
   # New pod appears almost immediately
   ```

**Key Difference**:
- **Kubernetes Self-Healing**: Maintains pod count via ReplicaSet
- **ArgoCD Self-Healing**: Syncs entire desired state from Git

### Test 3: Configuration Drift Detection

**Objective**: Detect manual resource changes and verify ArgoCD reverts them

**Test Procedure**:

1. **Get Current Pod Labels**
   ```bash
   kubectl get pod <pod-name> -n dev -o yaml | grep labels: -A 10
   ```

2. **Manually Add Label**
   ```bash
   kubectl label pod <pod-name> -n dev test-label=manual-change
   ```

3. **Verify Label Added**
   ```bash
   kubectl get pod <pod-name> -n dev -L test-label
   # Should show: manual-change
   ```

4. **Check ArgoCD Diff**
   ```bash
   argocd app diff python-app-dev
   # Shows the label discrepancy
   ```

5. **Self-Healing Reverts** (Within 3 minutes)
   ```bash
   kubectl get pod <pod-name> -n dev -L test-label
   # Label removed
   ```

**Evidence**: Label manually added, then automatically removed by ArgoCD

### Sync Behavior Documentation

#### When Does ArgoCD Sync?

1. **Automatic Polling** (Every 3 minutes)
   ```bash
   # Default polling interval
   argocd app wait <app-name> --sync
   ```

2. **Webhook Trigger** (Immediate)
   - GitHub push webhook calls ArgoCD
   - Immediate sync without waiting for 3-minute interval

3. **Manual Trigger**
   ```bash
   argocd app sync <app-name>
   # Immediate sync
   ```

4. **On Application Update**
   - When values files change
   - When Helm chart changes
   - When target revision changes

#### Sync Policy Options

**Manual Sync** (Prod):
```yaml
syncPolicy:
  syncOptions:
    - CreateNamespace=true
```
- No automatic syncs
- Requires explicit `argocd app sync` or UI click

**Auto-Sync** (Dev):
```yaml
syncPolicy:
  automated:
    prune: true
    selfHeal: true
  syncOptions:
    - CreateNamespace=true
```

**Options Explanation**:
- `automated.prune: true`: Delete resources removed from Git
- `automated.selfHeal: true`: Revert manual changes
- `syncOptions`: Additional sync options

#### What Triggers Sync?

| Event | Manual | Auto | Time |
|-------|--------|------|------|
| Git Push | ❌ | ✅ | 3 min |
| Webhook | ❌ | ✅ | <1 min |
| Manual Command | ✅ | ✅ | Immediate |
| Auto-sync Interval | ❌ | ✅ | 3 min |
| Resource Drift | ❌ | ✅ (if selfHeal) | 3 min |

### Configuration Drift Examples

**Example 1**: Replica Count Change
- Git: 1 replica
- Cluster: 5 replicas (manual scale)
- Result: ArgoCD reverts to 1 (if selfHeal enabled)

**Example 2**: Environment Variable
- Git: `DEBUG=false`
- Cluster: `DEBUG=true` (manual edit)
- Result: ArgoCD reverts to `DEBUG=false`

**Example 3**: Image Tag
- Git: `tag: "1.0"`
- Cluster: `tag: "1.1"` (manual update)
- Result: ArgoCD reverts to `1.0`

### Best Practices

1. **Dev Environment**
   - Enable auto-sync for faster feedback
   - Enable self-heal to prevent manual changes
   - Use latest image tags
   - Prune resources to keep namespace clean

2. **Prod Environment**
   - Manual sync for change control
   - Disable self-heal to prevent unexpected changes
   - Disable prune for safety
   - Use specific version tags

3. **General**
   - Always make changes in Git, not on cluster
   - Use separate branches for different environments
   - Monitor ArgoCD UI for sync status
   - Set up webhooks for immediate sync

---

## Application Manifests

### application.yaml

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/poeticlama/DevOps-Core-Course.git
    targetRevision: main
    path: app_python/k8s/devops-chart
    helm:
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

### application-dev.yaml

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/poeticlama/DevOps-Core-Course.git
    targetRevision: main
    path: app_python/k8s/devops-chart
    helm:
      valueFiles:
        - values-dev.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### application-prod.yaml

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/poeticlama/DevOps-Core-Course.git
    targetRevision: main
    path: app_python/k8s/devops-chart
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: prod
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

---

## Environment Comparison

### Development Environment

**Configuration** (`values-dev.yaml`):
- Replicas: 1 (minimal resource usage)
- Image: `latest` tag (always pull newest)
- Resource Limits: 100m CPU, 128Mi Memory
- Service: NodePort (local access)
- Probes: Lenient timeouts

**ArgoCD Policy**:
- Auto-sync enabled
- Self-heal enabled
- Prune enabled
- Immediate feedback on changes

**Use Case**:
- Developer testing
- Feature validation
- Quick feedback loop
- Resource efficiency

### Production Environment

**Configuration** (`values-prod.yaml`):
- Replicas: 5 (redundancy and capacity)
- Image: Specific version `1.0` tag
- Resource Limits: 500m CPU, 512Mi Memory
- Service: LoadBalancer (external access)
- Probes: Strict timeouts

**ArgoCD Policy**:
- Manual sync only
- No self-heal (prevent unexpected changes)
- No automatic prune
- Controlled deployments

**Use Case**:
- Production workloads
- High availability
- Stable versions
- Change control

---

## Troubleshooting

### Application Won't Sync

**Issue**: Application remains OutOfSync

**Solutions**:
1. Check Git repository connectivity
   ```bash
   argocd repo list
   ```

2. Verify repository credentials
   ```bash
   kubectl get secrets -n argocd | grep repository
   ```

3. Check Helm chart validity
   ```bash
   helm lint app_python/k8s/devops-chart
   ```

4. Force sync
   ```bash
   argocd app sync python-app --force
   ```

### Application Health is Degraded

**Issue**: Application shows Degraded health

**Solutions**:
1. Check pod status
   ```bash
   kubectl describe pod <pod-name> -n <namespace>
   ```

2. Check events
   ```bash
   kubectl get events -n <namespace>
   ```

3. Check logs
   ```bash
   kubectl logs <pod-name> -n <namespace>
   ```

### Cannot Access ArgoCD UI

**Issue**: Port forward connection refused

**Solutions**:
1. Verify port forward is running
   ```bash
   kubectl port-forward svc/argocd-server -n argocd 8080:443
   ```

2. Check if port 8080 is available
   ```bash
   netstat -an | grep 8080
   ```

3. Use different port if needed
   ```bash
   kubectl port-forward svc/argocd-server -n argocd 8888:443
   ```

---

## References

- [ArgoCD Official Documentation](https://argo-cd.readthedocs.io/)
- [ArgoCD Application CRD](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/)
- [Sync Policies & Options](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/)
- [GitOps Principles](https://opengitops.dev/)
- [Helm Chart Best Practices](https://helm.sh/docs/chart_best_practices/)

---

## Summary

This implementation demonstrates:
- ✅ ArgoCD installation and configuration
- ✅ Declarative application deployment via Application CRD
- ✅ Multi-environment support (dev/prod)
- ✅ Sync policies and auto-healing
- ✅ GitOps workflow integration
- ✅ Configuration drift detection and remediation

The application is now managed entirely through Git, with ArgoCD ensuring cluster state matches the desired state defined in the repository.

