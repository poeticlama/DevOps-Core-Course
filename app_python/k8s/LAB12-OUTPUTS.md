# Lab 12 - Example Outputs

## API Response Examples

### 1. Root Endpoint (`GET /`)

With visits counter included:

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI",
    "visits": 5
  },
  "system": {
    "hostname": "devops-chart-abc123-xyz",
    "platform": "Linux",
    "platform_version": "#1 SMP ...",
    "architecture": "x86_64",
    "cpu_count": 4,
    "python_version": "3.13.0"
  },
  "runtime": {
    "uptime_seconds": 342,
    "uptime_human": "0 hours, 5 minutes",
    "current_time": "2026-04-16T10:30:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "10.0.0.5",
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
      "path": "/visits",
      "method": "GET",
      "description": "Get total visit count"
    },
    {
      "path": "/metrics",
      "method": "GET",
      "description": "Prometheus metrics"
    }
  ]
}
```

### 2. Visits Endpoint (`GET /visits`)

```json
{
  "visits": 5,
  "timestamp": "2026-04-16T10:30:00.000000+00:00"
}
```

### 3. Health Endpoint (`GET /health`)

```json
{
  "status": "healthy",
  "timestamp": "2026-04-16T10:30:00.000000+00:00",
  "uptime_seconds": 342
}
```

## Kubernetes Verification Outputs

### ConfigMaps Created

```bash
$ kubectl get configmaps
NAME                       DATA   AGE
devops-dev-config         1      2m
devops-dev-env            5      2m
kube-root-ca.crt          1      10m
```

### ConfigMap Content (File-Based)

```bash
$ kubectl get configmap devops-dev-config -o yaml
apiVersion: v1
kind: ConfigMap
metadata:
  labels:
    app.kubernetes.io/chart: devops-chart-0.1.0
    app.kubernetes.io/instance: devops-dev
    app.kubernetes.io/name: devops-info-service
  name: devops-dev-config
  namespace: default
data:
  config.json: |
    {
      "appName": "DevOps Info Service",
      "environment": "production",
      "version": "1.0.0",
      "features": {
        "metricsEnabled": true,
        "healthCheckEnabled": true,
        "visitCounterEnabled": true
      },
      "logging": {
        "level": "INFO",
        "format": "json"
      },
      "server": {
        "port": 8080,
        "host": "0.0.0.0"
      }
    }
```

### ConfigMap Content (Environment Variables)

```bash
$ kubectl get configmap devops-dev-env -o yaml
apiVersion: v1
kind: ConfigMap
metadata:
  labels:
    app.kubernetes.io/chart: devops-chart-0.1.0
    app.kubernetes.io/instance: devops-dev
    app.kubernetes.io/name: devops-info-service
  name: devops-dev-env
  namespace: default
data:
  APP_ENV: "development"
  APP_NAME: "DevOps Info Service (Dev)"
  LOG_LEVEL: "DEBUG"
  METRICS_ENABLED: "true"
  VISITS_FILE_PATH: "/data/visits"
```

### PersistentVolumeClaim Status

```bash
$ kubectl get pvc
NAME                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
devops-dev-data      Bound    pvc-abc123de-f456-7890-ghij-klmnopqrstuv   500Mi      RWO            standard       2m
```

### PVC Detailed View

```bash
$ kubectl describe pvc devops-dev-data
Name:          devops-dev-data
Namespace:     default
StorageClass:  standard
Status:        Bound
Volume:        pvc-abc123de-f456-7890-ghij-klmnopqrstuv
Labels:        app.kubernetes.io/chart=devops-chart-0.1.0
               app.kubernetes.io/instance=devops-dev
               app.kubernetes.io/name=devops-info-service
Capacity:      500Mi
Access Modes:  RWO
VolumeMode:    Filesystem
Used By:       devops-dev-abc123-xyz
Events:
  Type    Reason                 Age   From                         Message
  ----    ------                 ----  ----                         -------
  Normal  ExternalProvisioning   2m    persistentvolume-controller  waiting for a volume to be created
  Normal  Provisioning           2m    ebs.csi.aws.com              External provisioning succeeded
  Normal  ProvisioningSucceeded  2m    persistentvolume-controller  Successfully provisioned volume using ebs.csi.aws.com
```

### Pod Environment Variables

```bash
$ kubectl exec -it devops-dev-abc123-xyz -- env | grep -E '^APP_|^LOG_|^VISITS_'
APP_NAME=DevOps Info Service (Dev)
APP_ENV=development
LOG_LEVEL=DEBUG
METRICS_ENABLED=true
VISITS_FILE_PATH=/data/visits
```

### Configuration File Inside Pod

```bash
$ kubectl exec -it devops-dev-abc123-xyz -- cat /etc/config/config.json
{
  "appName": "DevOps Info Service",
  "environment": "production",
  "version": "1.0.0",
  "features": {
    "metricsEnabled": true,
    "healthCheckEnabled": true,
    "visitCounterEnabled": true
  },
  "logging": {
    "level": "INFO",
    "format": "json"
  },
  "server": {
    "port": 8080,
    "host": "0.0.0.0"
  }
}
```

### Visits File Content

```bash
$ kubectl exec -it devops-dev-abc123-xyz -- ls -la /data
total 12
drwxrwxrwx 2 root root 4096 Apr 16 10:25 .
drwxr-xr-x 1 root root 4096 Apr 16 10:24 ..
-rw-r--r-- 1 appuser appuser   3 Apr 16 10:28 visits

$ kubectl exec -it devops-dev-abc123-xyz -- cat /data/visits
12
```

### Pod Volumes Configuration

```bash
$ kubectl describe pod devops-dev-abc123-xyz
Name:         devops-dev-abc123-xyz
Namespace:    default
...
Mounts:
  /data from data (rw)
  /etc/config from config (ro)
  /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-abcde (ro)

Volumes:
  config:
    Type:      ConfigMap (a volume populated by a ConfigMap)
    Name:      devops-dev-config
    Optional:  false
  data:
    Type:       PersistentVolumeClaim (a reference to a PersistentVolumeClaim in the same namespace)
    ClaimName:  devops-dev-data
    ReadOnly:   false
  kube-api-access-abcde:
    Type:                    Projected (all in one) (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    ConfigMapOptional:       <nil>
    DownwardAPI:             true
```

## Docker Compose Verification

### Volume Contents After Container Restart

**Before restart:**
```bash
$ docker-compose exec app curl http://localhost:8080/visits
{"visits":5,"timestamp":"2026-04-16T10:25:00.000000+00:00"}

$ cat ./data/visits
5
```

**After restart:**
```bash
$ docker-compose restart

$ docker-compose exec app curl http://localhost:8080/visits
{"visits":5,"timestamp":"2026-04-16T10:28:00.000000+00:00"}

$ cat ./data/visits
5
```

The visits counter persists across container restarts!

## Helm Chart Values

### Development Environment

```bash
$ helm get values devops-dev
replicaCount: 1
image:
  repository: poeticlama/devops-info-service
  tag: latest
  pullPolicy: Always
config:
  appName: DevOps Info Service (Dev)
  environment: development
  logLevel: DEBUG
  metricsEnabled: true
persistence:
  enabled: true
  size: 500Mi
  storageClass: null
```

### Production Environment

```bash
$ helm get values devops-prod
replicaCount: 5
image:
  repository: poeticlama/devops-info-service
  tag: '1.0'
  pullPolicy: IfNotPresent
config:
  appName: DevOps Info Service (Prod)
  environment: production
  logLevel: INFO
  metricsEnabled: true
persistence:
  enabled: true
  size: 10Gi
  storageClass: null
```

## Persistence Test Sequence

### Step 1: Check Initial Visits Count
```bash
$ curl http://localhost:8080/visits
{"visits":3,"timestamp":"2026-04-16T10:15:00.000000+00:00"}
```

### Step 2: Make Some Additional Requests
```bash
$ curl http://localhost:8080/
$ curl http://localhost:8080/
$ curl http://localhost:8080/visits
{"visits":6,"timestamp":"2026-04-16T10:16:00.000000+00:00"}
```

### Step 3: Delete the Pod
```bash
$ kubectl delete pod devops-dev-abc123-xyz
pod "devops-dev-abc123-xyz" deleted
```

### Step 4: Wait for New Pod to Start
```bash
$ kubectl get pods -l app.kubernetes.io/name=devops-info-service -w
NAME                    READY   STATUS    RESTARTS   AGE
devops-dev-xyz789-def   1/1     Running   0          5s
```

### Step 5: Verify Visits Counter Preserved
```bash
$ curl http://localhost:8080/visits
{"visits":6,"timestamp":"2026-04-16T10:17:00.000000+00:00"}
```

**Result:** ✅ Visits counter preserved across pod restart!

## Application Logs

### Startup Logs
```
{"timestamp": "2026-04-16T10:24:00.000000+00:00", "level": "INFO", "logger": "__main__", "message": "Initialized visits counter: 0"}
{"timestamp": "2026-04-16T10:24:00.000000+00:00", "level": "INFO", "logger": "__main__", "message": "DevOps Info Service starting up"}
```

### Request Logs
```
{"timestamp": "2026-04-16T10:25:00.000000+00:00", "level": "INFO", "logger": "__main__", "message": "HTTP request: GET / from 10.0.0.5"}
{"timestamp": "2026-04-16T10:25:00.000000+00:00", "level": "INFO", "logger": "__main__", "message": "HTTP response: GET / -> 200"}
{"timestamp": "2026-04-16T10:25:30.000000+00:00", "level": "INFO", "logger": "__main__", "message": "Visits endpoint accessed. Current count: 1"}
```

## File Structure Verification

```
app_python/
├── app.py                          # ✅ Updated with visits counter
├── docker-compose.yml              # ✅ NEW: Docker Compose with volumes
├── Dockerfile                      # ✅ Existing
├── README.md                       # ✅ Updated with new endpoints
├── requirements.txt                # ✅ Existing
├── k8s/
│   ├── CONFIGMAPS.md              # ✅ NEW: Complete documentation
│   ├── deployment.yml             # ✅ Existing (standalone)
│   ├── service.yml                # ✅ Existing (standalone)
│   ├── HELM.md                    # ✅ Existing
│   ├── README.md                  # ✅ Existing
│   ├── SECRETS.md                 # ✅ Existing
│   └── devops-chart/
│       ├── Chart.yaml             # ✅ Existing
│       ├── values.yaml            # ✅ Updated with config & persistence
│       ├── values-dev.yaml        # ✅ Updated with config & persistence
│       ├── values-prod.yaml       # ✅ Updated with config & persistence
│       ├── files/
│       │   └── config.json        # ✅ NEW: Application configuration
│       └── templates/
│           ├── configmap.yaml     # ✅ NEW: ConfigMap templates
│           ├── deployment.yaml    # ✅ Updated with volume mounts
│           ├── pvc.yaml           # ✅ NEW: PersistentVolumeClaim
│           ├── service.yaml       # ✅ Existing
│           ├── secrets.yaml       # ✅ Existing
│           ├── hooks/             # ✅ Existing
│           └── _helpers.tpl       # ✅ Existing
└── tests/                         # ✅ Existing
```

