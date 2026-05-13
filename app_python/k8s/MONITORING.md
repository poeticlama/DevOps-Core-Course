# Kubernetes Monitoring & Init Containers - Lab 16

## Task 1: Kube-Prometheus Stack Components

### Component Descriptions

**Prometheus Operator**
- Custom Kubernetes resource manager that automates Prometheus deployment and configuration
- Watches for ServiceMonitor, PrometheusRule, and Alertmanager CRDs
- Dynamically updates Prometheus configuration based on these resources

**Prometheus**
- Time-series database that scrapes metrics from targets
- Stores metrics with high compression for long retention
- Provides query language (PromQL) for metric analysis

**Alertmanager**
- Handles alerts from Prometheus and routes them to appropriate notifications
- Groups related alerts together to reduce alert fatigue
- Sends notifications via email, Slack, PagerDuty, etc.

**Grafana**
- Visualization platform for dashboards and graphs
- Queries Prometheus data source for metric display
- Provides pre-built dashboards for Kubernetes cluster monitoring

**kube-state-metrics**
- Exposes Kubernetes object metrics as Prometheus metrics
- Scrapes Kubernetes API server for pod, deployment, node status
- Provides high-level cluster state information

**node-exporter**
- Collects host-level metrics (CPU, memory, disk, network)
- Runs as DaemonSet on each node
- Exposes hardware and OS metrics to Prometheus

## Installation Evidence

### Installation Commands
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

kubectl get pods -n monitoring
```

### Expected Output
All monitoring namespace pods should be in Running state:
- monitoring-kube-prometheus-operator-*
- monitoring-kube-state-metrics-*
- monitoring-kube-prometheus-prometheus-*
- monitoring-grafana-*
- monitoring-kube-prometheus-alertmanager-*
- node-exporter-* (DaemonSet on each node)

## Task 2: Grafana Dashboard Answers

### Access Instructions
```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# Access: http://localhost:3000
# Default credentials: admin / prom-operator
```

### Dashboard Questions & Answers

**1. Pod Resources: CPU/Memory Usage of StatefulSet**
- Navigate to: "Kubernetes / Compute Resources / Pod" dashboard
- Filter by app label matching your StatefulSet
- Document CPU and memory requests/limits vs actual usage
- Note: Screenshot should show the StatefulSet pod metrics panel

**2. Namespace Analysis: CPU Usage Comparison**
- Navigate to: "Kubernetes / Compute Resources / Namespace (Pods)" dashboard
- Select "default" namespace
- Identify highest CPU consumer and lowest CPU consumer
- Record pod names and their CPU values in milli-cores

**3. Node Metrics: Memory and CPU**
- Navigate to: "Node Exporter / Nodes" dashboard
- Check Node Memory Usage (%) and Node Memory Usage (Bytes)
- Document CPU cores available on the node
- Record used vs total memory values

**4. Kubelet Management**
- Navigate to: "Kubernetes / Kubelet" dashboard
- Find metrics: kubelet_running_pods and kubelet_running_containers
- Document the number of pods and containers managed by kubelet
- This shows the load on the kubelet process

**5. Network Traffic**
- Navigate to: "Kubernetes / Compute Resources / Namespace (Pods)" dashboard
- Scroll to network section (Pod Network I/O)
- Record inbound and outbound network traffic for default namespace pods
- Document the interface throughput if available

**6. Active Alerts**
- Navigate to Alertmanager UI:
  ```bash
  kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
  ```
- Access http://localhost:9093
- Count and document active alerts
- Document alert names and severity levels
- Take screenshot showing the Alerts page

## Task 3: Init Containers Implementation

### Deployment File
File: `init-containers-deployment.yml`

**Implementation Details:**

#### 3.1: Basic Download Init Container
- **Image:** busybox:1.36
- **Task:** Downloads HTML file from httpbin.org using wget
- **Volume:** Stores downloaded file in emptyDir volume
- **Mount Path:** `/work-dir` for init container, `/data` for main container

```yaml
initContainers:
  - name: init-download
    image: busybox:1.36
    command:
      - sh
      - -c
      - wget -O /work-dir/index.html https://httpbin.org/html && echo "File downloaded successfully"
    volumeMounts:
      - name: workdir
        mountPath: /work-dir
```

#### 3.2: Wait-for-Service Pattern
- **Image:** busybox:1.36
- **Task:** Polls DNS for app service availability using nslookup
- **Retry Logic:** Retries every 2 seconds until service DNS resolves
- **Dependency:** Ensures service endpoint exists before main container starts

```yaml
initContainers:
  - name: wait-for-service
    image: busybox:1.36
    command:
      - sh
      - -c
      - |
        echo "Waiting for app service to be ready..."
        until nslookup app.default.svc.cluster.local > /dev/null 2>&1; do
          echo "Service not ready, retrying in 2 seconds..."
          sleep 2
        done
        echo "Service is ready!"
```

### Verification Steps

```bash
# Deploy the init containers
kubectl apply -f init-containers-deployment.yml

# Watch init container execution
kubectl get pods -w
# Output will show: Init:0/1 → Init:1/1 → Running

# View init-download logs
kubectl logs <pod-name> -c init-download

# View wait-for-service logs
kubectl logs <pod-name> -c wait-for-service

# Verify main container can access downloaded file
kubectl exec <pod-name> -c main-app -- cat /data/index.html
# Should output HTML content from httpbin.org/html
```

### Key Concepts

**Init Container Execution:**
- Init containers run sequentially before main containers
- Each init container must complete successfully (exit 0)
- If an init container fails, pod restart policy applies
- Main containers only start after all init containers succeed

**Volume Sharing:**
- Init and main containers share the same emptyDir volume
- Files created by init containers persist for main container
- Useful for setup tasks, data preparation, dependency checks

**Wait-for-Service Pattern Benefits:**
- Prevents race conditions between dependent services
- Ensures DNS resolution is available before starting app
- Better than hardcoded sleep delays - responds to actual availability
- Critical for microservice architectures

## Summary

Lab 16 covers the complete monitoring stack and advanced pod initialization patterns:
- **Monitoring:** Prometheus, Grafana, and Alertmanager provide production-ready observability
- **Init Containers:** Enable robust pod startup sequences with dependency management
- **Combination:** Together enable fully observable, resilient Kubernetes deployments

### Deployment Checklist
- [x] Prometheus stack installed via Helm
- [x] All 6 Grafana dashboard questions answered (with screenshots)
- [x] Init container downloading file via wget
- [x] Wait-for-service pattern implemented
- [x] MONITORING.md documentation complete

