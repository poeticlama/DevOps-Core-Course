# LAB10 — Helm Chart for DevOps Info Service

## 1. Helm Chart Overview

### Purpose

A Helm chart was created to package the DevOps Info Service Kubernetes manifests into a reusable, configurable, and deployable package. Helm charts enable templating, environment-specific configurations, and lifecycle management for Kubernetes applications.

### Chart Structure

The chart follows Helm best practices with the following directory structure:

```
devops-chart/
├── Chart.yaml                 # Chart metadata and version
├── values.yaml               # Default configuration values
├── values-dev.yaml           # Development environment overrides
├── values-prod.yaml          # Production environment overrides
├── templates/
│   ├── _helpers.tpl         # Template helper functions
│   ├── deployment.yaml       # Kubernetes Deployment template
│   ├── service.yaml          # Kubernetes Service template
│   └── hooks/
│       ├── pre-install-job.yaml    # Pre-installation hook
│       └── post-install-job.yaml   # Post-installation hook
```

---

## 2. Chart Configuration

### 2.1 Chart.yaml

The Chart.yaml file defines the chart metadata:

```yaml
apiVersion: v2
name: devops-info-service
description: Helm chart for DevOps Info Service - a FastAPI-based information service
type: application
version: 0.1.0
appVersion: "1.0"
```

**Key fields:**

* **apiVersion**: Helm API version (v2 for Helm 3)
* **name**: Chart name used for identification
* **description**: Human-readable chart description
* **version**: Semantic versioning of the chart itself
* **appVersion**: Version of the application being deployed

---

### 2.2 Default Values (values.yaml)

The default values file contains standard configuration for all environments:

**Replica Management:**
```yaml
replicaCount: 3
```

**Image Configuration:**
```yaml
image:
  repository: poeticlama/devops-info-service
  tag: "1.0"
  pullPolicy: IfNotPresent
```

**Service Configuration:**
```yaml
service:
  type: NodePort
  port: 80
  targetPort: 8080
  nodePort: 30080
```

**Resource Limits:**
```yaml
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

**Health Checks:**

Probes are configured for automated health monitoring:

* **Liveness Probe**: Checks if the container is alive; restarts if unhealthy
* **Readiness Probe**: Checks if the pod is ready to receive traffic

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 2
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 3
  timeoutSeconds: 1
  failureThreshold: 2
```

**Security Context:**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
```

---

## 3. Environment-Specific Values

### 3.1 Development Environment (values-dev.yaml)

Development configuration prioritizes ease of use and debugging:

```yaml
replicaCount: 1
image:
  tag: "latest"
  pullPolicy: Always
service:
  type: NodePort
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
namespace: default
```

**Development Focus:**

* Single replica for resource efficiency
* `latest` tag for quick iteration
* Lenient probe settings for development
* NodePort service for local access

---

### 3.2 Production Environment (values-prod.yaml)

Production configuration prioritizes reliability and performance:

```yaml
replicaCount: 5
image:
  tag: "1.0"
  pullPolicy: IfNotPresent
service:
  type: LoadBalancer
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi
namespace: production
```

**Production Focus:**

* Higher replica count (5) for availability
* Specific version tags for stability
* LoadBalancer service for external exposure
* Higher resource limits for performance
* Stricter probe settings for reliability
* Zero-downtime rolling updates

---

## 4. Helm Templates

### 4.1 Template Helpers (_helpers.tpl)

Reusable template definitions reduce code duplication:

```yaml
{{- define "devops-chart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
```

**Helper Functions:**

* `devops-chart.name`: Returns the chart name
* `devops-chart.fullname`: Generates fully qualified resource names
* `devops-chart.labels`: Common Kubernetes labels
* `devops-chart.selectorLabels`: Labels for pod selection

---

### 4.2 Deployment Template (deployment.yaml)

The Deployment template uses Go templating syntax to generate dynamic Kubernetes manifests:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "devops-chart.fullname" . }}
  namespace: {{ .Values.namespace }}
  labels:
    {{- include "devops-chart.labels" . | nindent 4 }}

spec:
  replicas: {{ .Values.replicaCount }}
  strategy:
    {{- toYaml .Values.strategy | nindent 4 }}
```

**Template Features:**

* Uses `{{ }}` syntax for variable interpolation
* Includes helper functions for consistent naming
* References values.yaml for configuration
* Supports dynamic resource configuration

---

### 4.3 Service Template (service.yaml)

The Service template handles network exposure:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "devops-chart.fullname" . }}
  namespace: {{ .Values.namespace }}

spec:
  type: {{ .Values.service.type }}
  ports:
  - name: http
    port: {{ .Values.service.port }}
    targetPort: {{ .Values.service.targetPort }}
    {{- if eq .Values.service.type "NodePort" }}
    nodePort: {{ .Values.service.nodePort }}
    {{- end }}
```

**Service Flexibility:**

* Supports multiple service types (NodePort, LoadBalancer, ClusterIP)
* Conditional nodePort assignment for NodePort services
* Dynamic port configuration

---

## 5. Helm Hooks

### 5.1 Pre-Install Hook (pre-install-job.yaml)

Executes validation before chart installation:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "{{ include "devops-chart.fullname" . }}-pre-install"
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
```

**Purpose:**

* Validates prerequisites before deployment
* Performs pre-installation checks
* Ensures cluster readiness
* Runs before any other resources are created

**Hook Execution:**

* Hook weight: `-5` (runs early in the sequence)
* Delete policy: `hook-succeeded` (cleans up after successful execution)

---

### 5.2 Post-Install Hook (post-install-job.yaml)

Performs validation and smoke tests after installation:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "{{ include "devops-chart.fullname" . }}-post-install"
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
```

**Purpose:**

* Executes smoke tests after deployment
* Validates service health
* Confirms successful installation
* Provides deployment confirmation

**Hook Execution:**

* Hook weight: `5` (runs after normal resources)
* Delete policy: `hook-succeeded` (cleans up after successful execution)

---

## 6. Chart Usage

### 6.1 Installation Commands

**Install with default values:**
```bash
helm install devops-release ./devops-chart
```

**Install in development environment:**
```bash
helm install devops-release ./devops-chart -f devops-chart/values-dev.yaml
```

**Install in production environment:**
```bash
helm install devops-release ./devops-chart -f devops-chart/values-prod.yaml
```

**Upgrade existing release:**
```bash
helm upgrade devops-release ./devops-chart -f devops-chart/values-prod.yaml
```

**Dry-run mode (preview changes):**
```bash
helm install devops-release ./devops-chart --dry-run --debug
```

---

### 6.2 Chart Validation

**Lint the chart for errors:**
```bash
helm lint ./devops-chart
```

**Template rendering preview:**
```bash
helm template devops-release ./devops-chart
```

**Render with custom values:**
```bash
helm template devops-release ./devops-chart -f devops-chart/values-prod.yaml
```

---

## 7. Key Features

### 7.1 Templating Benefits

* **Code Reuse**: Template helpers eliminate duplication
* **Consistency**: Ensures uniform resource naming and labeling
* **Maintainability**: Single source of truth for configuration
* **Flexibility**: Easy adaptation for different environments

### 7.2 Environment-Specific Configuration

* **Development**: Minimal resources, rapid iteration
* **Production**: High availability, performance optimized
* **Separation of Concerns**: Environment differences are explicit

### 7.3 Lifecycle Hooks

* **Pre-Install**: Validates prerequisites
* **Post-Install**: Performs verification tests
* **Automatic Cleanup**: Hooks are removed after execution

### 7.4 Health Management

* **Liveness Probes**: Automatic container restart on failure
* **Readiness Probes**: Prevents traffic to unhealthy pods
* **Gradual Rollouts**: Rolling updates with controlled disruption

---

## 8. Best Practices Applied

### 8.1 Chart Structure

* Follows official Helm chart conventions
* Clear separation between templates and values
* Environment-specific values files for scalability
* Proper documentation and metadata

### 8.2 Security

* Non-root container execution
* Explicit security contexts
* Resource limits to prevent resource exhaustion
* Namespace isolation for production

### 8.3 Reliability

* Multiple replicas for high availability
* Rolling update strategy with zero downtime
* Health checks for automated recovery
* Hook-based validation

### 8.4 Operability

* Human-readable configuration
* Consistent naming conventions
* Easy environment switching
* Comprehensive hook implementation

---

## 9. Challenges & Solutions

### Challenge 1: Template Complexity

**Issue:** Balancing flexibility with readability in templates

**Solution:** 
* Created reusable helper functions in `_helpers.tpl`
* Used meaningful variable names in values files
* Documented each configuration option

---

### Challenge 2: Environment Differences

**Issue:** Managing significant differences between dev and prod

**Solution:**
* Created environment-specific values files (values-dev.yaml, values-prod.yaml)
* Used Helm's `-f` flag to merge configurations
* Maintained clear separation of concerns

---

### Challenge 3: Hook Sequencing

**Issue:** Ensuring hooks run in correct order

**Solution:**
* Used hook weights for sequencing
* Pre-install weight: `-5` (runs first)
* Post-install weight: `5` (runs after resources)

---

## 10. Files Created

```
app_python/k8s/devops-chart/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── deployment.yaml
│   ├── service.yaml
│   └── hooks/
│       ├── pre-install-job.yaml
│       └── post-install-job.yaml
```

---

## 11. Conclusion

A complete, production-ready Helm chart was successfully created for the DevOps Info Service. The chart includes:

* ✅ Templated Kubernetes manifests (Deployment and Service)
* ✅ Default values for standard configuration
* ✅ Environment-specific values for development and production
* ✅ Template helper functions for code reuse
* ✅ Pre-install and post-install hooks for lifecycle management
* ✅ Comprehensive documentation

The chart is ready for deployment across multiple environments and can be easily maintained and extended for future requirements.

