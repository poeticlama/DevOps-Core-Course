# Lab 14 — Progressive Delivery with Argo Rollouts

## Overview

This document covers the implementation of progressive delivery strategies using Argo Rollouts in the DevOps Info Service application. We have implemented both **canary** and **blue-green** deployment strategies with automatic traffic management and rollback capabilities.

---

## Task 1 — Argo Rollouts Fundamentals

### Installation and Verification

#### Controller Installation
To install Argo Rollouts, execute the following commands:

```bash
# Create namespace for Argo Rollouts
kubectl create namespace argo-rollouts

# Install Argo Rollouts controller
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Verify controller is running
kubectl get pods -n argo-rollouts
```

You should see the `argo-rollouts` controller pod running with status `Running`.

#### kubectl Plugin Installation
For CLI management of rollouts:

**macOS (using Homebrew):**
```bash
brew install argoproj/tap/kubectl-argo-rollouts
```

**Linux:**
```bash
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts
```

**Verification:**
```bash
kubectl argo rollouts version
```

#### Dashboard Installation
To deploy the Argo Rollouts Dashboard for visualization:

```bash
# Install dashboard
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

# Access dashboard via port-forward
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
# Open browser at http://localhost:3100
```

### Rollout vs Deployment: Key Differences

| Feature | Deployment | Rollout |
|---------|-----------|---------|
| **Kind** | `apps/v1 - Deployment` | `argoproj.io/v1alpha1 - Rollout` |
| **Basic Updates** | Rolling update, recreate | Same as Deployment |
| **Progressive Delivery** | Not supported | Canary, Blue-Green, Traffic shifting |
| **Traffic Shifting** | No built-in support | Native traffic splitting per step |
| **Analysis** | Manual | Integrated metrics-based analysis |
| **Automatic Rollback** | Manual/health-based | Policy-driven rollback |
| **Pod Template** | Identical | Identical |
| **Selector/Labels** | Identical | Identical |

**Key Additions in Rollout:**
- `strategy.canary` - Configure canary-specific steps and traffic management
- `strategy.blueGreen` - Configure blue-green deployment with active/preview services
- `analysis` - Metrics-based automated promotion/rollback (optional)

---

## Task 2 — Canary Deployment

### Overview
Canary deployments gradually shift traffic to the new version in percentage steps, allowing you to detect issues early before full rollout.

### Implementation

**File:** `app_python/k8s/devops-chart/templates/rollout-canary.yaml`

#### Canary Strategy Configuration
```yaml
strategy:
  canary:
    steps:
      - setWeight: 20      # Start with 20% traffic to new version
      - pause: {}          # Manual promotion required
      - setWeight: 40      # Increase to 40%
      - pause:
          duration: 30s    # Auto-continue after 30 seconds
      - setWeight: 60      # Increase to 60%
      - pause:
          duration: 30s    # Auto-continue after 30 seconds
      - setWeight: 80      # Increase to 80%
      - pause:
          duration: 30s    # Auto-continue after 30 seconds
      - setWeight: 100     # Complete rollout to 100%
```

**Traffic Flow Progression:**
1. **Step 1:** 80% old version → 20% new version (Manual promotion)
2. **Step 2:** 60% old → 40% new (30s pause)
3. **Step 3:** 40% old → 60% new (30s pause)
4. **Step 4:** 20% old → 80% new (30s pause)
5. **Step 5:** 100% new version (Complete)

### Testing Canary Deployment

#### Deployment Steps:
```bash
# Enable canary strategy in values
helm install devops-app ./devops-chart \
  --set rollout.enabled=true \
  --set rollout.strategy=canary

# Or update existing installation
helm upgrade devops-app ./devops-chart \
  --set rollout.enabled=true \
  --set rollout.strategy=canary

# Watch rollout progress in dashboard
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

#### CLI Commands:
```bash
# Watch rollout status in real-time
kubectl argo rollouts get rollout devops-info-service -w

# Promote to next step (at manual pause)
kubectl argo rollouts promote devops-info-service

# Abort rollout and return to stable version
kubectl argo rollouts abort devops-info-service

# Check detailed rollout status
kubectl argo rollouts status devops-info-service
```

### Testing Rollback

**Procedure:**
1. Start a canary deployment (trigger new image update)
2. Wait for the rollout to reach the first pause at 20%
3. Test the new version using separate traffic/monitoring
4. If issues are detected, abort the rollout:
   ```bash
   kubectl argo rollouts abort devops-info-service
   ```
5. Traffic immediately returns to 100% old version

**Key Benefit:** Canary allows early detection while minimizing blast radius. Issues affect only 20-80% of users instead of all users.

---

## Task 3 — Blue-Green Deployment

### Overview
Blue-green deployment maintains two identical environments:
- **Blue (Active):** Current production version serving all traffic
- **Green (Preview):** New version ready for testing with zero traffic

When satisfied, you switch all traffic instantly from blue to green (or rollback to blue).

### Implementation

**Files:**
- `app_python/k8s/devops-chart/templates/rollout-bluegreen.yaml`
- `app_python/k8s/devops-chart/templates/service-preview.yaml`

#### Blue-Green Strategy Configuration
```yaml
strategy:
  blueGreen:
    activeService: devops-info-service           # Service for production (blue/green)
    previewService: devops-info-service-preview  # Service for new version (green when deploying)
    autoPromotionEnabled: false                  # Requires manual promotion
    # autoPromotionSeconds: 30                   # Alternative: auto-promote after 30s
```

#### Service Separation
- **Active Service (`devops-info-service`):**
  - Routes to currently stable version pods
  - Serves production traffic
  - Endpoints updated during promotion

- **Preview Service (`devops-info-service-preview`):**
  - Routes to new version pods
  - Available for testing/validation
  - Can be accessed via NodePort 30081 (separate from active 30080)

### Testing Blue-Green Flow

#### Setup:
```bash
# Enable blue-green strategy
helm install devops-app ./devops-chart \
  --set rollout.enabled=true \
  --set rollout.strategy=bluegreen

# Or update
helm upgrade devops-app ./devops-chart \
  --set rollout.enabled=true \
  --set rollout.strategy=bluegreen
```

#### Testing Procedure:

**1. Verify Initial Deployment (Blue)**
```bash
# Access active service (blue - current production)
kubectl port-forward svc/devops-info-service -n default 8080:80

# Test application at http://localhost:8080
# Note the version/timestamp
```

**2. Trigger New Deployment (Green)**
```bash
# Update image tag or configuration
helm upgrade devops-app ./devops-chart \
  --set rollout.enabled=true \
  --set rollout.strategy=bluegreen \
  --set image.tag="1.1"

# Watch rollout status
kubectl argo rollouts get rollout devops-info-service -w
```

**3. Test Green (New Version)**
```bash
# Access preview service in separate terminal
kubectl port-forward svc/devops-info-service-preview -n default 8081:80

# Test new version at http://localhost:8081
# Verify new features/changes work correctly
# Active service still serving old version at 8080
```

**4. Promote Green to Active**
```bash
# When satisfied, promote green to active
kubectl argo rollouts promote devops-info-service

# Active service now routes to green (new) version
# Old blue pods are retained for quick rollback
```

**5. Verify Promotion**
```bash
# Access active service again
kubectl port-forward svc/devops-info-service -n default 8080:80

# Confirm you're now seeing the new version
# Response should match what you saw in preview service
```

**6. Instant Rollback (if needed)**
```bash
# Rollback to previous (blue) version
kubectl argo rollouts abort devops-info-service

# Active service immediately routes back to old version
# Instant traffic switch - no gradual shift
```

### Key CLI Commands

```bash
# Watch blue-green rollout status
kubectl argo rollouts get rollout devops-info-service -w

# Describe rollout (includes current active/preview endpoints)
kubectl argo rollouts describe rollout devops-info-service

# Promote green to blue (make new version active)
kubectl argo rollouts promote devops-info-service

# Abort and return to previous version
kubectl argo rollouts abort devops-info-service

# Retry after abort
kubectl argo rollouts retry rollout devops-info-service

# Check all rollouts in cluster
kubectl argo rollouts list rollouts

# Restart a rollout
kubectl argo rollouts restart rollout devops-info-service
```

---

## Strategy Comparison

### Canary Deployment
**Use When:**
- Risk of breaking changes is moderate
- Need early detection with partial blast radius
- Have monitoring/metrics available
- Want gradual rollback option
- Resources are limited (don't need 2x capacity)

**Pros:**
- Detects issues early (only 20% affected initially)
- Gradual traffic shift reduces risk
- Can abort mid-rollout for rollback
- Resource efficient (shared capacity)
- Good for API/backend service changes

**Cons:**
- Longer deployment time (multiple pause steps)
- Requires manual intervention at each pause
- Complex monitoring/analysis needed
- Harder to detect datacenter-wide failures
- Mixed traffic can cause subtle bugs

### Blue-Green Deployment
**Use When:**
- Need instant rollback capability
- Can afford 2x resource capacity during deployment
- Deploying to multiple regions/datacenters
- UI changes or frontend updates
- Need to validate entire system before switching

**Pros:**
- Instant switch between versions (zero-transition time)
- Complete validation before production traffic
- Simple rollback (just switch pointer)
- Two identical production environments
- Good for major feature releases

**Cons:**
- Requires 2x resources during deployment
- Entire environment must pass before promotion
- Migrations/schema changes need careful planning
- Database compatibility issues persist

### Recommendation by Scenario

| Scenario | Strategy | Reason |
|----------|----------|--------|
| API endpoint changes | Canary | Early error detection, gradual traffic |
| Minor bug fixes | Blue-Green | Quick rollback if issue missed in preview |
| Major UI redesign | Blue-Green | User sees consistent old or new, not mixed |
| Database schema change | Blue-Green | Validate entire system with new schema |
| Configuration changes | Canary | Low risk, gradual rollout safe |
| Performance optimization | Canary | Watch metrics at each step |
| Multi-region deployment | Blue-Green | Ensure consistency across regions |
| Microservice update | Canary | Detect compatibility issues early |

---

## File Structure

### Helm Chart Files Created/Modified

**New Files:**
```
app_python/k8s/devops-chart/templates/
├── rollout-canary.yaml          # Canary strategy Rollout definition
├── rollout-bluegreen.yaml       # Blue-green strategy Rollout definition
└── service-preview.yaml         # Preview service for blue-green
```

**Modified Files:**
```
app_python/k8s/devops-chart/
└── values.yaml                  # Added rollout configuration section
```

### Configuration Key: `rollout.strategy`

Set in `values.yaml` or via Helm CLI:

```bash
# Canary deployment
--set rollout.enabled=true --set rollout.strategy=canary

# Blue-green deployment
--set rollout.enabled=true --set rollout.strategy=bluegreen

# No progressive delivery (standard Deployment)
--set rollout.enabled=false
```

---

## Useful Commands Reference

### Installation & Verification
```bash
# Install Argo Rollouts
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Verify installation
kubectl get pods -n argo-rollouts
kubectl argo rollouts version

# Install dashboard
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

### Rollout Management
```bash
# Deploy with Helm (canary)
helm install devops-app ./devops-chart --set rollout.enabled=true --set rollout.strategy=canary

# Deploy with Helm (blue-green)
helm install devops-app ./devops-chart --set rollout.enabled=true --set rollout.strategy=bluegreen

# List all rollouts
kubectl argo rollouts list rollouts
kubectl argo rollouts list rollouts -n <namespace>

# Watch rollout progress
kubectl argo rollouts get rollout <rollout-name> -w
kubectl argo rollouts status <rollout-name>

# Detailed information
kubectl argo rollouts describe rollout <rollout-name>
kubectl get rollout <rollout-name> -o yaml
```

### During Deployment
```bash
# Promote to next step (canary)
kubectl argo rollouts promote <rollout-name>

# Abort rollout and return to stable
kubectl argo rollouts abort <rollout-name>

# Retry after abort
kubectl argo rollouts retry rollout <rollout-name>

# Restart rollout (triggers new deployment)
kubectl argo rollouts restart rollout <rollout-name>
```

### Debugging
```bash
# Check rollout events
kubectl describe rollout <rollout-name>

# Check associated ReplicaSets
kubectl get replicasets -l app=<app-name>

# Check pod status
kubectl get pods -l app=<app-name>

# View logs
kubectl logs -l app=<app-name> -f

# Port-forward for testing
kubectl port-forward svc/<service-name> 8080:80
```

---

## Integration with Existing Components

### Compatibility with ArgoCD (Lab 13)
- Rollout templates are compatible with ArgoCD
- Define Rollout resources in Helm chart as done here
- ArgoCD will create/manage Rollouts same as Deployments
- Application CRD works with both Deployments and Rollouts

### ServiceMonitor Integration (Lab 16)
- Rollouts expose same metrics as Deployments
- Prometheus ServiceMonitor configuration unchanged
- Monitor Rollout progress via standard Kubernetes metrics

### ConfigMaps & Secrets
- Rollout pod templates use same ConfigMaps/Secrets as Deployment
- No changes needed to config/secrets management

---

## Summary

**Lab 14 Completion Checklist:**

✅ **Task 1 - Fundamentals:**
- Argo Rollouts controller installation procedure documented
- Dashboard installation and access documented
- Key differences between Rollout and Deployment explained

✅ **Task 2 - Canary:**
- Canary strategy implemented in `rollout-canary.yaml`
- Progressive steps configured (20% → 100%)
- Manual promotion and automatic pauses configured
- Testing procedure documented

✅ **Task 3 - Blue-Green:**
- Blue-green strategy implemented in `rollout-bluegreen.yaml`
- Preview service created in `service-preview.yaml`
- Active and preview service separation documented
- Promotion and rollback procedures documented

✅ **Task 4 - Documentation:**
- This ROLLOUTS.md file provides comprehensive coverage
- Strategy comparison included
- CLI commands reference provided
- Practical testing procedures included

---

## Next Steps

- **Lab 15:** StatefulSets for stateful applications
- **Lab 16:** Monitoring and metrics analysis for auto-rollback
- **Lab 17:** Multi-environment deployments with Rollouts

---

**Implementation Complete** ✅


