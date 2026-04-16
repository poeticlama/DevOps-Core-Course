# Lab 12: ConfigMaps, Persistent Volumes & Persistent Volume Claims

## Overview

This lab demonstrates how to use Kubernetes ConfigMaps for application configuration management and PersistentVolumeClaims (PVC) for data persistence across pod restarts.

## Key Concepts

### ConfigMaps
ConfigMaps are Kubernetes objects used to store non-sensitive configuration data as key-value pairs or files. They decouple configuration from container images, making applications more portable.

**Types of ConfigMaps in this lab:**
1. **File-based ConfigMap** - Contains the entire `config.json` file
2. **Literal ConfigMap** - Contains individual environment variables

### Persistent Volumes & Persistent Volume Claims
- **PersistentVolume (PV)** - Storage resource provisioned by administrator
- **PersistentVolumeClaim (PVC)** - Storage request by a pod
- **PVC binds to PV** to provide persistent storage across pod lifecycle

**Use case:** The visits counter needs to persist across pod restarts and deployments.

## Implementation Details

### 1. Application Changes (app.py)

Added visits counter functionality with file-based persistence:

```python
VISITS_FILE = Path(os.getenv("VISITS_FILE_PATH", "/data/visits"))
visits_lock = threading.Lock()

def read_visits_count():
    """Read visits count from file, return 0 if file doesn't exist"""
    try:
        if VISITS_FILE.exists():
            with open(VISITS_FILE, 'r') as f:
                return int(f.read().strip())
    except (ValueError, IOError) as e:
        app_logger.warning(f"Error reading visits file: {e}")
    return 0

def increment_visits():
    """Increment visits count and persist to file"""
    with visits_lock:
        current_count = read_visits_count()
        new_count = current_count + 1
        try:
            with open(VISITS_FILE, 'w') as f:
                f.write(str(new_count))
        except IOError as e:
            app_logger.error(f"Error writing visits file: {e}")
        return new_count
```

**New Endpoints:**
- `GET /visits` - Returns current visits count

**Modified Endpoints:**
- `GET /` - Now increments visits counter with each call

### 2. ConfigMap Templates

#### File-based ConfigMap (`templates/configmap.yaml`)

Contains the application configuration file:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: devops-chart-config
  namespace: default
data:
  config.json: |-
    {
      "appName": "DevOps Info Service",
      "environment": "production",
      "version": "1.0.0",
      "features": {...}
    }
```

The configuration file is mounted at `/etc/config/config.json` in the pod.

#### Environment ConfigMap

Contains individual environment variables:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: devops-chart-env
data:
  APP_NAME: "DevOps Info Service"
  APP_ENV: "production"
  LOG_LEVEL: "INFO"
  METRICS_ENABLED: "true"
  VISITS_FILE_PATH: "/data/visits"
```

### 3. PersistentVolumeClaim (`templates/pvc.yaml`)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: devops-chart-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

**Key Points:**
- `accessModes: ReadWriteOnce` - Can be mounted by single pod as read-write
- Requests 1Gi storage (configurable per environment)
- Storage class left unspecified to use cluster default

### 4. Deployment Updates

The deployment template now includes:

```yaml
spec:
  volumes:
  - name: config
    configMap:
      name: devops-chart-config
  - name: data
    persistentVolumeClaim:
      claimName: devops-chart-data
  
  containers:
  - name: devops-info-service
    envFrom:
    - configMapRef:
        name: devops-chart-env
    - secretRef:
        name: devops-chart-credentials
    
    volumeMounts:
    - name: config
      mountPath: /etc/config
    - name: data
      mountPath: /data
```

### 5. Values Configuration

**values.yaml:**
```yaml
config:
  appName: "DevOps Info Service"
  environment: "production"
  logLevel: "INFO"
  metricsEnabled: true

persistence:
  enabled: true
  size: 1Gi
  storageClass: null
```

**values-dev.yaml:**
```yaml
config:
  appName: "DevOps Info Service (Dev)"
  environment: "development"
  logLevel: "DEBUG"
  metricsEnabled: true

persistence:
  enabled: true
  size: 500Mi
  storageClass: null
```

**values-prod.yaml:**
```yaml
config:
  appName: "DevOps Info Service (Prod)"
  environment: "production"
  logLevel: "INFO"
  metricsEnabled: true

persistence:
  enabled: true
  size: 10Gi
  storageClass: null
```

## Deployment Instructions

### Prerequisites
- Kubernetes cluster (minikube, Docker Desktop, or cloud provider)
- `kubectl` configured
- Helm 3.x installed

### Deploy to Development

```bash
cd app_python/k8s
helm install devops-dev devops-chart -f devops-chart/values-dev.yaml
```

### Deploy to Production

```bash
cd app_python/k8s
helm install devops-prod devops-chart -f devops-chart/values-prod.yaml -n production --create-namespace
```

### Verify Deployment

```bash
# Check if pod is running
kubectl get pods -l app.kubernetes.io/name=devops-info-service

# Check ConfigMaps
kubectl get configmaps
kubectl describe configmap devops-dev-config

# Check PVC
kubectl get pvc
kubectl describe pvc devops-dev-data

# Port forward to access service
kubectl port-forward svc/devops-dev 8080:80

# Test endpoints
curl http://localhost:8080/
curl http://localhost:8080/visits
curl http://localhost:8080/health
```

### Verify Persistence

```bash
# Get initial visits count
curl http://localhost:8080/visits

# Delete the pod to force restart
kubectl delete pod -l app.kubernetes.io/name=devops-info-service

# Pod will be recreated automatically (ReplicaSet)
# Verify visits counter is preserved
curl http://localhost:8080/visits
```

### Update Application Configuration

To change configuration values without rebuilding the image:

```bash
# Update values
helm upgrade devops-dev devops-chart \
  -f devops-chart/values-dev.yaml \
  --set config.logLevel=WARNING
```

## File Structure

```
app_python/
├── app.py                          # Updated with visits counter
├── docker-compose.yml              # Docker Compose with volume mounting
├── k8s/
│   └── devops-chart/
│       ├── Chart.yaml
│       ├── values.yaml             # Updated with config & persistence
│       ├── values-dev.yaml         # Updated with config & persistence
│       ├── values-prod.yaml        # Updated with config & persistence
│       ├── files/
│       │   └── config.json         # Application configuration file
│       └── templates/
│           ├── configmap.yaml      # NEW: ConfigMap templates
│           ├── deployment.yaml     # Updated with volume mounts
│           └── pvc.yaml            # NEW: PersistentVolumeClaim
└── README.md                       # Updated with persistence info
```

## Troubleshooting

### ConfigMap not being loaded
```bash
# Verify ConfigMap exists
kubectl get configmap devops-dev-config -o yaml

# Check pod environment variables
kubectl exec -it <pod-name> -- env | grep APP_
```

### PVC stuck in Pending
```bash
# Check PVC status
kubectl describe pvc devops-dev-data

# Common causes:
# - No storage class available
# - Insufficient storage capacity
# - Waiting for node to be ready
```

### Visits counter not persisting
```bash
# Check volume mount in pod
kubectl exec -it <pod-name> -- ls -la /data

# Verify file permissions
kubectl exec -it <pod-name> -- cat /data/visits
```

## Key Takeaways

✅ **ConfigMaps** decouple configuration from container images  
✅ **File-based ConfigMaps** can store entire configuration files  
✅ **Environment ConfigMaps** provide individual variables  
✅ **PersistentVolumeClaims** enable stateful applications in Kubernetes  
✅ **Different storage sizes** per environment (dev: 500Mi, prod: 10Gi)  
✅ **Thread-safe operations** ensure data integrity with concurrent access  
✅ **Automatic pod recreation** preserves data with persistent storage  

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | INFO | Application logging level |
| `VISITS_FILE_PATH` | /data/visits | Path to visits counter file |
| `APP_NAME` | DevOps Info Service | Application display name |
| `APP_ENV` | production | Environment name |
| `METRICS_ENABLED` | true | Enable Prometheus metrics |

## References

- [Kubernetes ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Kubernetes PersistentVolumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Helm ConfigMaps](https://helm.sh/docs/chart_best_practices/templates/)
- [Helm Values](https://helm.sh/docs/chart_template_guide/values/)

