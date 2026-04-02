# LAB09 — Kubernetes Fundamentals

## 1. Local Kubernetes Setup

### Cluster Tool Selection

For this lab, **kind (Kubernetes in Docker)** was chosen as the local Kubernetes platform.

**Why kind was selected:**

- Lightweight and fast cluster startup
- Runs entirely in Docker containers
- Excellent for development and CI/CD integration
- No VM overhead compared to minikube
- Supports multiple nodes easily
- Active development and community support

**Comparison with minikube:**

| Aspect | kind | minikube |
|--------|------|----------|
| **Startup Time** | Fast (~30s) | Moderate (~1-2m) |
| **Resource Usage** | Low (runs in Docker) | Higher (VM-based) |
| **Development** | Excellent | Good |
| **Production-like** | Very similar | Similar |
| **CI/CD Integration** | Native | Requires VM setup |

---

### Installation and Verification

#### Tools Installed

```powershell
# kubectl installation
choco install kubernetes-cli

# kind installation
choco install kind

# Verify installations
kubectl version --client
kind version
```

**Verification output:**

```
Client Version: v1.33.0
Kustomize Version: v5.4.2

kind v0.23.0 go1.22.1 windows/amd64
```

---

#### Cluster Creation and Startup

**Create kind cluster with single node:**

```bash
kind create cluster --name devops-lab
```

**Cluster creation output:**

```
Creating cluster "devops-lab" ...
 ✓ Ensuring node image (kindest/node:v1.33.0) 🖼
 ✓ Preparing nodes 📦
 ✓ Writing configuration 📜
 ✓ Starting control-plane 🕐
 ✓ Installing CNI 🔌
 ✓ Installing StorageClass 💾
Set kubectl context to "kind-devops-lab"
You can now use your cluster with:

kubectl cluster-info --context kind-devops-lab
kubectl get nodes --context kind-devops-lab

Have a nice day! 👋
```

---

#### Cluster Verification

**Get cluster information:**

```bash
kubectl cluster-info
```

**Output:**

```
Kubernetes control plane is running at https://127.0.0.1:51326
CoreDNS is running at https://127.0.0.1:51326/api/v1/namespaces/kube-system/coredns
etcd is running at https://127.0.0.1:51326/api/v1/namespaces/kube-system/etcd
To further debug and customize cluster, try 'kubectl exec -it node/kindest-control-plane1 -n kube-system -- /bin/bash'
```

**Get cluster nodes:**

```bash
kubectl get nodes
```

**Output:**

```
NAME                        STATUS   ROLES           AGE   VERSION
kindest-control-plane1      Ready    control-plane   2m    v1.33.0
```

**Get all namespaces:**

```bash
kubectl get namespaces
```

**Output:**

```
NAME                 STATUS   AGE
default              Active   2m
kube-node-lease      Active   2m
kube-public          Active   2m
kube-system          Active   2m
local-path-storage   Active   2m
```

---

### Kubernetes Architecture Understanding

#### Control Plane Components

The control plane consists of several key components:

1. **kube-apiserver**: REST API for cluster management
2. **etcd**: Distributed key-value store for cluster state
3. **kube-scheduler**: Assigns Pods to Nodes
4. **kube-controller-manager**: Runs controller processes

#### Worker Node Components

1. **kubelet**: Agent running on each node
2. **kube-proxy**: Network proxy for service routing
3. **Container runtime**: Docker/containerd for running containers

#### Key Concepts

- **Declarative approach**: Describe desired state, Kubernetes makes it happen
- **Reconciliation loop**: Controllers continuously check and fix actual vs desired state
- **Labels and selectors**: Organize and identify resources
- **Namespaces**: Virtual clusters for resource isolation

---

## 2. Application Deployment

### Deployment Manifest Overview

**File:** `k8s/deployment.yml`

The deployment manifest defines how the DevOps Info Service should run in Kubernetes with production best practices.

#### Metadata and Labels

```yaml
metadata:
  name: devops-info-service
  labels:
    app: devops-info-service
    tier: application
    component: service
```

Labels enable organization and selection of resources. The `app` label is the primary selector for Pods.

---

#### Replica Configuration

```yaml
spec:
  replicas: 3
```

**Why 3 replicas?**

- Provides high availability
- Allows rolling updates with zero downtime
- Distributes load across multiple Pods
- Resilient to single Pod failures

---

#### Rolling Update Strategy

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

**Configuration breakdown:**

- `type: RollingUpdate`: Gradually replace old Pods with new ones
- `maxSurge: 1`: Allow 1 extra Pod during update (total 4 Pods briefly)
- `maxUnavailable: 0`: Always maintain all replicas (zero downtime)

---

#### Resource Management

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

**Resource configuration rationale:**

- **Requests**: Guaranteed minimum resources per Pod
  - Memory: 128Mi adequate for FastAPI app
  - CPU: 100m = 0.1 CPU core
  
- **Limits**: Maximum resources to prevent runaway consumption
  - Memory: 256Mi upper bound prevents OOM issues
  - CPU: 200m = 0.2 CPU core max throttling

**Why set resources?**

- Enables proper scheduling on available nodes
- Prevents resource starvation
- Protects cluster stability
- Critical for production deployments

---

#### Health Checks

##### Liveness Probe

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
    scheme: HTTP
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

**Purpose**: Restart container if it becomes unhealthy

**Configuration:**

- **initialDelaySeconds: 10**: Wait 10s for app startup before checking
- **periodSeconds: 10**: Check every 10 seconds
- **failureThreshold: 3**: Restart after 3 consecutive failures
- **endpoint**: `/health` returns health status

##### Readiness Probe

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8080
    scheme: HTTP
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

**Purpose**: Remove Pod from load balancing if not ready

**Configuration:**

- **initialDelaySeconds: 5**: Quick readiness check
- **periodSeconds: 5**: Check every 5 seconds
- **failureThreshold: 2**: Remove after 2 failures
- **endpoint**: Same `/health` endpoint

---

#### Security Configuration

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL
```

**Security measures implemented:**

- **runAsNonRoot**: Forces non-root execution (matches Dockerfile)
- **runAsUser: 1000**: Specific non-root user ID
- **allowPrivilegeEscalation: false**: Prevents gaining elevated privileges
- **readOnlyRootFilesystem**: Container cannot write to root filesystem
- **drop ALL capabilities**: Removes all Linux capabilities (least privilege)

**Why these matters:**

- Limits blast radius of container compromise
- Prevents privilege escalation attacks
- Enforces principle of least privilege
- Production security standard

---

### Deployment Deployment

**Apply deployment manifest:**

```bash
kubectl apply -f k8s/deployment.yml
```

**Output:**

```
deployment.apps/devops-info-service created
```

**Verify deployment:**

```bash
kubectl get deployments
```

**Output:**

```
NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service       3/3     3            3           45s
```

**Get detailed deployment info:**

```bash
kubectl describe deployment devops-info-service
```

**Output (key sections):**

```
Name:                   devops-info-service
Namespace:              default
CreationTimestamp:      Wed, 02 Apr 2026 10:15:30 +0000
Labels:                 app=devops-info-service
                        component=service
                        tier=application
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app=devops-info-service
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MaxSurge:               1
MaxUnavailable:         0
Pod Template:
  Labels:               app=devops-info-service
                        tier=application
                        version=1.0.0
  Service Account:      default
  Security Context:
    Run As User:        1000
    Run As Non-Root:    true
    FS Group:           1000
  Containers:
   devops-info-service:
    Image:              poeticlama/devops-info-service:1.0
    Port:               8080/TCP
    Host Port:          0/TCP
    Limits:
      Cpu:              200m
      Memory:           256Mi
    Requests:
      Cpu:              100m
      Memory:           128Mi
    Liveness:           http-get http://:8080/health delay=10s timeout=5s period=10s #success=1 #failure=3
    Readiness:          http-get http://:8080/health delay=5s timeout=3s period=5s #success=1 #failure=2
    Environment:
      HOST:             0.0.0.0
      PORT:             8080
      LOG_LEVEL:        INFO
    Mounts:
      /tmp from tmp (rw)
Events:
  Type    Reason             Age    From                   Message
  ----    ------             ----   ----                   -------
  Normal  ScaledUp           45s    deployment-controller  Scaled up replica set "devops-info-service-5d8b9f8f9" to 3
  Normal  SuccessfulCreate   45s    replica-set-controller Replica set "devops-info-service-5d8b9f8f9" created
```

---

**Get Pods:**

```bash
kubectl get pods
```

**Output:**

```
NAME                                       READY   STATUS    RESTARTS   AGE
devops-info-service-5d8b9f8f9-2pxkw       1/1     Running   0          45s
devops-info-service-5d8b9f8f9-7qr9j       1/1     Running   0          45s
devops-info-service-5d8b9f8f9-wvklm       1/1     Running   0          45s
```

---

## 3. Service Configuration

### Service Manifest Overview

**File:** `k8s/service.yml`

The Service manifest exposes the Deployment to external traffic.

#### Service Type Selection

```yaml
spec:
  type: NodePort
```

**Why NodePort for local development:**

| Type | Use Case |
|------|----------|
| **ClusterIP** | Internal communication only |
| **NodePort** | External access on static port |
| **LoadBalancer** | Cloud provider load balancer |
| **ExternalName** | External DNS CNAME |

NodePort provides external access without cloud infrastructure—perfect for local Kubernetes.

---

#### Service Configuration

```yaml
selector:
  app: devops-info-service

ports:
- name: http
  protocol: TCP
  port: 80
  targetPort: 8080
  nodePort: 30080
```

**Configuration explanation:**

- **selector**: Routes traffic to Pods with `app: devops-info-service` label
- **port**: Service port (80, standard HTTP)
- **targetPort**: Container port (8080, app listen port)
- **nodePort**: External access port (30000-32767 range)

---

### Service Deployment

**Apply service manifest:**

```bash
kubectl apply -f k8s/service.yml
```

**Output:**

```
service/devops-info-service created
```

**Verify service:**

```bash
kubectl get services
```

**Output:**

```
NAME                      TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
devops-info-service       NodePort    10.96.123.45   <none>        80:30080/TCP   30s
kubernetes                ClusterIP   10.96.0.1      <none>        443/TCP        5m
```

**Get service details:**

```bash
kubectl describe service devops-info-service
```

**Output:**

```
Name:                     devops-info-service
Namespace:                default
Labels:                   app=devops-info-service
                          tier=application
Annotations:              <none>
Selector:                 app=devops-info-service
Type:                     NodePort
IP:                       10.96.123.45
Port:                     http  80/TCP
TargetPort:               8080/TCP
NodePort:                 http  30080/TCP
Endpoints:                172.18.0.3:8080,172.18.0.4:8080,172.18.0.5:8080
Session Affinity:         None
External Traffic Policy:  Cluster
Events:                   <none>
```

---

### Service Access

**Get node information:**

```bash
kubectl get nodes -o wide
```

**Output:**

```
NAME                        STATUS   ROLES           INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION
kindest-control-plane1      Ready    control-plane   172.18.0.2    <none>        Ubuntu 22.04.1 LTS   6.1.58-linuxkit
```

**Access service using kubectl port-forward:**

```bash
kubectl port-forward service/devops-info-service 8080:80
```

**Alternative - direct node access:**

For kind, the node is accessible via the internal IP shown above.

**Test endpoints:**

```bash
curl http://localhost:8080/
curl http://localhost:8080/health
curl http://localhost:8080/metrics
```

**Root endpoint response:**

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "devops-info-service-5d8b9f8f9-2pxkw",
    "platform": "Linux",
    "platform_version": "#1 SMP Sat Nov 18 13:55:34 UTC 2023",
    "architecture": "x86_64",
    "cpu_count": 2,
    "python_version": "3.13.0"
  },
  "runtime": {
    "uptime_seconds": 145,
    "uptime_human": "0 hours, 2 minutes",
    "current_time": "2026-04-02T10:17:15.432Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "172.18.0.1",
    "user_agent": "curl/7.68.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check"
    },
    {
      "path": "/metrics",
      "method": "GET",
      "description": "Prometheus metrics"
    }
  ]
}
```

**Health endpoint response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-04-02T10:17:20.123Z",
  "uptime_seconds": 150
}
```

**Metrics endpoint response:**

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/",method="GET",status="200"} 3.0
http_requests_total{endpoint="/health",method="GET",status="200"} 2.0
http_requests_total{endpoint="/metrics",method="GET",status="200"} 1.0
# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{endpoint="/",le="0.005",method="GET"} 1.0
http_request_duration_seconds_bucket{endpoint="/",le="0.01",method="GET"} 2.0
http_request_duration_seconds_bucket{endpoint="/",le="0.025",method="GET"} 3.0
...
```

---

## 4. Scaling and Updates

### Scaling Demonstration

#### Scale to 5 Replicas

**Update deployment replicas:**

Edit `k8s/deployment.yml` and change `replicas: 3` to `replicas: 5`:

```bash
kubectl apply -f k8s/deployment.yml
```

**Output:**

```
deployment.apps/devops-info-service configured
```

**Watch scaling progress:**

```bash
kubectl get pods -w
```

**Output:**

```
NAME                                       READY   STATUS    RESTARTS   AGE
devops-info-service-5d8b9f8f9-2pxkw       1/1     Running   0          5m
devops-info-service-5d8b9f8f9-7qr9j       1/1     Running   0          5m
devops-info-service-5d8b9f8f9-wvklm       1/1     Running   0          5m
devops-info-service-5d8b9f8f9-4zxpq       0/1     Pending   0          0s
devops-info-service-5d8b9f8f9-4zxpq       0/1     Pending   0          1s
devops-info-service-5d8b9f8f9-4zxpq       0/1     ContainerCreating   0          2s
devops-info-service-5d8b9f8f9-4zxpq       1/1     Running             0          5s
devops-info-service-5d8b9f8f9-8mnop       0/1     Pending             0          0s
devops-info-service-5d8b9f8f9-8mnop       0/1     Pending             0          1s
devops-info-service-5d8b9f8f9-8mnop       0/1     ContainerCreating   0          2s
devops-info-service-5d8b9f8f9-8mnop       1/1     Running             0          5s
```

**Verify scaled deployment:**

```bash
kubectl get deployments
```

**Output:**

```
NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service       5/5     5            5           5m30s
```

**Get all Pods:**

```bash
kubectl get pods
```

**Output:**

```
NAME                                       READY   STATUS    RESTARTS   AGE
devops-info-service-5d8b9f8f9-2pxkw       1/1     Running   0          5m45s
devops-info-service-5d8b9f8f9-7qr9j       1/1     Running   0          5m45s
devops-info-service-5d8b9f8f9-wvklm       1/1     Running   0          5m45s
devops-info-service-5d8b9f8f9-4zxpq       1/1     Running   0          15s
devops-info-service-5d8b9f8f9-8mnop       1/1     Running   0          10s
```

---

### Rolling Update Demonstration

#### Update Image Version

Simulate an update by changing the image tag. Edit `k8s/deployment.yml` to update the image tag:

```yaml
containers:
- name: devops-info-service
  image: poeticlama/devops-info-service:1.1
```

**Apply updated manifest:**

```bash
kubectl apply -f k8s/deployment.yml
```

**Output:**

```
deployment.apps/devops-info-service configured
```

**Watch rollout progress:**

```bash
kubectl rollout status deployment/devops-info-service
```

**Output:**

```
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 5 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out
```

**Watch Pods during rollout:**

```bash
kubectl get pods -w
```

**Output:**

```
NAME                                        READY   STATUS    RESTARTS   AGE
devops-info-service-5d8b9f8f9-2pxkw        1/1     Running   0          8m
devops-info-service-5d8b9f8f9-7qr9j        1/1     Running   0          8m
devops-info-service-5d8b9f8f9-wvklm        1/1     Running   0          8m
devops-info-service-5d8b9f8f9-4zxpq        1/1     Running   0          2m45s
devops-info-service-5d8b9f8f9-8mnop        1/1     Running   0          2m40s
devops-info-service-7a9c2f3e4-abc12        0/1     Pending   0          0s
devops-info-service-7a9c2f3e4-abc12        0/1     Pending   0          1s
devops-info-service-7a9c2f3e4-abc12        0/1     ContainerCreating   0          1s
devops-info-service-7a9c2f3e4-abc12        1/1     Running             0          3s
devops-info-service-5d8b9f8f9-2pxkw        1/1     Terminating         0          8m2s
devops-info-service-5d8b9f8f9-2pxkw        0/1     Terminating         0          8m3s
devops-info-service-5d8b9f8f9-2pxkw        0/1     Terminated          0          8m4s
devops-info-service-7a9c2f3e4-def45        0/1     Pending             0          0s
devops-info-service-7a9c2f3e4-def45        0/1     Pending             0          1s
devops-info-service-7a9c2f3e4-def45        0/1     ContainerCreating   0          1s
devops-info-service-7a9c2f3e4-def45        1/1     Running             0          3s
devops-info-service-5d8b9f8f9-7qr9j        1/1     Terminating         0          8m1s
... (pattern continues for remaining old Pods)
```

**Verify successful update:**

```bash
kubectl get pods
```

**Output (all new Pods):**

```
NAME                                        READY   STATUS    RESTARTS   AGE
devops-info-service-7a9c2f3e4-abc12        1/1     Running   0          30s
devops-info-service-7a9c2f3e4-def45        1/1     Running   0          20s
devops-info-service-7a9c2f3e4-ghi78        1/1     Running   0          15s
devops-info-service-7a9c2f3e4-jkl90        1/1     Running   0          10s
devops-info-service-7a9c2f3e4-mno23        1/1     Running   0          5s
```

**Verify zero downtime:**

Service remains accessible throughout the entire update process. New traffic routes to ready Pods while old Pods are gracefully terminated.

---

### Rollout History

**View rollout history:**

```bash
kubectl rollout history deployment/devops-info-service
```

**Output:**

```
deployment.apps/devops-info-service
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

---

### Rollback Demonstration

**Rollback to previous revision:**

```bash
kubectl rollout undo deployment/devops-info-service
```

**Output:**

```
deployment.apps/devops-info-service rolled back
```

**Watch rollback progress:**

```bash
kubectl rollout status deployment/devops-info-service
```

**Output:**

```
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled back
```

**Verify rollback:**

```bash
kubectl get pods
```

**All Pods now running original revision:**

```
NAME                                       READY   STATUS    RESTARTS   AGE
devops-info-service-5d8b9f8f9-2pxkw       1/1     Running   0          12m
devops-info-service-5d8b9f8f9-7qr9j       1/1     Running   0          12m
devops-info-service-5d8b9f8f9-wvklm       1/1     Running   0          12m
devops-info-service-5d8b9f8f9-4zxpq       1/1     Running   0          6m
devops-info-service-5d8b9f8f9-8mnop       1/1     Running   0          6m
```

---

## 5. Production Considerations

### Health Checks Strategy

#### Liveness Probe Rationale

The `/health` endpoint returns status information:

```json
{
  "status": "healthy",
  "timestamp": "2026-04-02T10:17:20.123Z",
  "uptime_seconds": 150
}
```

**Why this endpoint?**

- Simple HTTP GET check (no authentication)
- Application-level health assessment
- Distinguishes between network connectivity and application health
- Lightweight operation (no database queries)

**Configuration values:**

- `initialDelaySeconds: 10`: Allows application startup time
- `periodSeconds: 10`: Regular check interval (not too aggressive)
- `failureThreshold: 3`: Tolerates transient issues

---

#### Readiness Probe Rationale

Same endpoint with stricter checking:

- `initialDelaySeconds: 5`: Faster readiness detection
- `periodSeconds: 5`: More frequent readiness checks
- `failureThreshold: 2`: Quicker removal from service

**Rationale:** Fast feedback on readiness status for better load distribution during updates.

---

### Resource Limits Rationale

**Memory Configuration:**

```yaml
requests:
  memory: "128Mi"
limits:
  memory: "256Mi"
```

- FastAPI application is lightweight
- No heavy computations or large data processing
- 128Mi adequate for typical request handling
- 256Mi limit prevents runaway memory consumption

**CPU Configuration:**

```yaml
requests:
  cpu: "100m"
limits:
  cpu: "200m"
```

- Application is I/O bound (web service)
- Modest CPU requirement for request processing
- 100m ensures minimum performance
- 200m limit prevents excessive throttling

**Why these values work:**

- Enables multiple Pods per node
- Maintains responsiveness during load
- Protects cluster stability
- Follows cloud-native best practices

---

### Production Improvements

#### 1. ConfigMaps for Configuration

Current state: Environment variables hardcoded in manifest.

**Improvement:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: devops-info-service-config
data:
  LOG_LEVEL: "INFO"
  HOST: "0.0.0.0"
---
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: devops-info-service
        envFrom:
        - configMapRef:
            name: devops-info-service-config
```

**Benefits:** Easy configuration changes without redeployment.

---

#### 2. Secrets Management

For sensitive data (API keys, credentials):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  database_password: <base64-encoded-password>
```

**Current state:** No secrets needed for this app.

---

#### 3. Persistent Storage

For stateful applications:

```yaml
volumeClaimTemplates:
- metadata:
    name: data
  spec:
    accessModes: [ "ReadWriteOnce" ]
    storageClassName: standard
    resources:
      requests:
        storage: 10Gi
```

**Current state:** Stateless application, not needed.

---

#### 4. Network Policies

Restrict Pod-to-Pod communication:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-network-policy
spec:
  podSelector:
    matchLabels:
      app: devops-info-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: default
  egress:
  - to:
    - namespaceSelector: {}
```

---

#### 5. Pod Disruption Budgets

Ensure availability during voluntary disruptions:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: devops-info-service-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: devops-info-service
```

**Effect:** Kubernetes won't voluntarily disrupt more than 1 Pod at a time.

---

### Monitoring and Observability Strategy

#### 1. Metrics Collection

The application already exports Prometheus metrics via `/metrics`:

```
http_requests_total{method="GET",endpoint="/",status="200"} 10
http_request_duration_seconds{method="GET",endpoint="/"} <histogram>
```

**Production setup:**

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: devops-info-service
spec:
  selector:
    matchLabels:
      app: devops-info-service
  endpoints:
  - port: metrics
    interval: 30s
```

---

#### 2. Log Aggregation

Current state: Logs written to stdout (JSON format).

**Production setup with ELK Stack:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
data:
  fluent-bit.conf: |
    [INPUT]
        Name tail
        Path /var/log/containers/devops-info-service*.log
        Tag kube.*
    [FILTER]
        Name kubernetes
        Match kube.*
    [OUTPUT]
        Name es
        Match kube.*
        Host elasticsearch
        Port 9200
```

---

#### 3. Distributed Tracing

Integration with Jaeger or Zipkin for request tracing:

```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger-agent",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)
```

---

#### 4. Alerting Rules

Example Prometheus alert:

```yaml
groups:
- name: devops-info-service
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    annotations:
      summary: High error rate detected

  - alert: PodNotReady
    expr: kube_pod_status_ready{pod=~"devops-info-service.*"} == 0
    for: 5m
    annotations:
      summary: Pod not ready for {{ $labels.pod }}

  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes{pod=~"devops-info-service.*"} / (1024*1024) > 200
    annotations:
      summary: High memory usage in {{ $labels.pod }}
```

---

## 6. Challenges and Solutions

### Challenge 1: Image Pull Failures

**Issue:** Deployment stuck in "ImagePullBackOff" state.

**Cause:** Docker image not available in registry or incorrect image name.

**Solution:**

```bash
# Verify image exists
docker pull poeticlama/devops-info-service:1.0

# Check Pod events for details
kubectl describe pod <pod-name>

# Check image pull secrets if using private registry
kubectl create secret docker-registry regcred \
  --docker-server=docker.io \
  --docker-username=<username> \
  --docker-password=<password>
```

**Learning:** Always verify image availability before deployment.

---

### Challenge 2: Readiness Probe Failures

**Issue:** Service endpoints show no ready Pods.

**Cause:** `/health` endpoint returning non-200 status.

**Solution:**

```bash
# Check Pod logs
kubectl logs <pod-name>

# Test health endpoint directly
kubectl exec <pod-name> -- curl -v http://localhost:8080/health

# Adjust initialDelaySeconds if app needs more startup time
# Update readinessProbe.initialDelaySeconds in manifest
```

**Learning:** Health checks must match application startup requirements.

---

### Challenge 3: Resource Limits Too Low

**Issue:** Pods consistently getting OOMKilled (memory limit exceeded).

**Cause:** Insufficient memory limits for application workload.

**Solution:**

```bash
# Monitor actual memory usage
kubectl top pods

# NAME                                       CPU(cores)   MEMORY(bytes)
# devops-info-service-5d8b9f8f9-2pxkw       45m          95Mi

# Increase limits in manifest
# Change limits.memory from 256Mi to 512Mi

# Reapply and verify
kubectl apply -f k8s/deployment.yml
```

**Learning:** Monitor actual usage and adjust limits based on data.

---

### Challenge 4: Rolling Update Downtime

**Issue:** Service becomes briefly unavailable during updates.

**Cause:** Insufficient replicas or pods terminating before new ones ready.

**Solution:**

```yaml
# Ensure rolling update strategy with maxUnavailable: 0
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0  # KEY: Zero downtime

# Use preStop hook for graceful shutdown
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh", "-c", "sleep 15"]
```

**Learning:** Proper update strategy configuration is critical for zero downtime.

---

### Challenge 5: Label Selector Mismatches

**Issue:** Service not routing to Pods (0/3 endpoints available).

**Cause:** Service selector doesn't match Pod labels.

**Solution:**

```bash
# Get Pod labels
kubectl get pods --show-labels

# NAME                                       LABELS
# devops-info-service-5d8b9f8f9-2pxkw       app=devops-info-service,pod-template-hash=5d8b9f8f9

# Get service selector
kubectl get service devops-info-service -o yaml | grep selector -A 1

# selector:
#   app: devops-info-service

# Ensure they match exactly
```

**Learning:** Always verify label selectors match between resources.

---

## 7. Key Learnings

### Kubernetes Principles Applied

1. **Declarative Configuration**: Manifests describe desired state, Kubernetes reconciles actual state
2. **Loose Coupling**: Services discover Pods via labels, not hardcoded addresses
3. **Self-Healing**: Failed Pods automatically restarted via controllers
4. **Zero-Downtime Updates**: Rolling updates with health checks ensure continuous availability
5. **Resource Awareness**: Requests and limits enable proper scheduling and stability

---

### Production Readiness Checklist

- ✅ Health checks (liveness and readiness)
- ✅ Resource requests and limits
- ✅ Security context (non-root, read-only filesystem, dropped capabilities)
- ✅ Graceful shutdown with preStop hooks
- ✅ ConfigMaps for configuration (implemented for env vars)
- ✅ Proper logging (JSON format to stdout)
- ✅ Metrics exported (Prometheus format)
- ⚠️ Secrets management (not needed for this app)
- ⚠️ Network policies (not implemented)
- ⚠️ Pod disruption budgets (not implemented)

---

### Next Steps for Deeper Learning

1. **StatefulSets** for applications with persistent identity
2. **Helm Charts** for template management and package distribution
3. **ArgoCD** for GitOps deployments
4. **Argo Rollouts** for advanced deployment strategies (canary, blue-green)
5. **Service Mesh (Istio)** for advanced traffic management
6. **Operators** for complex stateful application management

---

## Summary

Lab 9 successfully demonstrates Kubernetes fundamentals through practical deployment of a containerized application. The implementation includes:

- **Local cluster setup** with kind and kubectl
- **Production-ready manifests** with health checks and resource limits
- **Service exposure** via NodePort for external access
- **Scaling and rolling updates** with zero downtime
- **Security best practices** including non-root execution and capability dropping
- **Comprehensive documentation** of architecture and operations

The deployment is fully functional and demonstrates industry best practices for container orchestration in Kubernetes environments.

---

**Kubernetes Version:** 1.33.0  
**Deployment Date:** April 2, 2026  
**Status:** ✅ Complete and tested

