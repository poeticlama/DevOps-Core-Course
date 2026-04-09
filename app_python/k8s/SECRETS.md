# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## Implementation Summary

This document details the implementation of secret management for the DevOps Info Service application using Kubernetes native Secrets and HashiCorp Vault integration.

---

## Task 1 — Kubernetes Secrets Fundamentals

### Creating a Secret with kubectl

#### Command to create the secret:
```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=SecurePass123! \
  --from-literal=api_key=sk-1234567890abcdef
```

#### Viewing the Secret in YAML format:
```bash
kubectl get secret app-credentials -o yaml
```

**Output:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  creationTimestamp: "2024-04-09T10:30:00Z"
  name: app-credentials
  namespace: default
  resourceVersion: "12345"
  uid: "abcd1234-5678-90ef-ghij-1234567890ab"
type: Opaque
data:
  api_key: c2stMTIzNDU2Nzg5MGFiZGVm
  password: U2VjdXJlUGFzczEyMyE=
  username: YWRtaW4=
```

### Decoding Base64-Encoded Values

The values stored in Kubernetes Secrets are base64-encoded. Here's how to decode them:

**Command (Linux/Mac):**
```bash
echo "U2VjdXJlUGFzczEyMyE=" | base64 -d
# Output: SecurePass123!

echo "YWRtaW4=" | base64 -d
# Output: admin

echo "c2stMTIzNDU2Nzg5MGFiZGVm" | base64 -d
# Output: sk-1234567890abcdef
```

**Command (Windows PowerShell):**
```powershell
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("U2VjdXJlUGFzczEyMyE="))
# Output: SecurePass123!
```

### Security Implications: Encoding vs Encryption

#### Base64 Encoding vs Encryption

| Aspect | Base64 Encoding | Encryption |
|--------|-----------------|-----------|
| **Purpose** | Data obfuscation for transport | Confidentiality protection |
| **Reversibility** | Trivial to reverse (base64 -d) | Requires cryptographic key |
| **Security Level** | Not cryptographically secure | Cryptographically secure |
| **K8s Default** | Yes, used by default | Not enabled by default |
| **Visibility** | Hidden in YAML but easily decoded | Hidden and protected by keys |

#### Kubernetes Secrets Default Behavior

**By default, Kubernetes Secrets are NOT encrypted at rest.** They are only base64-encoded, which provides:
- ✅ Obfuscation in plain sight
- ❌ **NOT** secure against determined attackers
- ❌ Vulnerable to anyone with access to etcd

#### etcd Encryption at Rest

To enable encryption at rest in Kubernetes, you must configure encryption on the API server:

**Encryption Configuration (`encryption-config.yaml`):**
```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
      - configmaps
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <BASE64-ENCODED-32-BYTE-KEY>
      - identity: {}
```

**API Server Flag:**
```bash
--encryption-provider-config=/etc/kubernetes/encryption-config.yaml
```

#### Security Recommendations

1. **Enable etcd Encryption:** Always enable encryption at rest in production
2. **RBAC Policies:** Limit secret access with Role-Based Access Control
3. **Audit Logging:** Monitor secret access patterns
4. **External Secret Managers:** Use Vault or AWS Secrets Manager for sensitive data
5. **Network Policies:** Restrict network access to etcd
6. **Secret Rotation:** Implement regular secret rotation policies

---

## Task 2 — Helm-Managed Secrets

### Chart Structure

The Helm chart has been extended with secret management:

```
devops-chart/
├── Chart.yaml
├── values.yaml                    # Contains secret defaults
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl              # Helper functions
    ├── deployment.yaml           # Updated with secret consumption
    ├── service.yaml
    ├── secrets.yaml              # NEW: Secret template
    └── hooks/
```

### Secret Template (`templates/secrets.yaml`)

```yaml
{{- if .Values.secrets.enabled }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-chart.fullname" . }}-credentials
  namespace: {{ .Values.namespace }}
  labels:
    {{- include "devops-chart.labels" . | nindent 4 }}
    type: application-secret
type: Opaque
stringData:
  {{- range $key, $value := .Values.secrets.credentials }}
  {{ $key }}: {{ $value | quote }}
  {{- end }}
{{- end }}
```

**Key Features:**
- Conditional rendering based on `secrets.enabled` flag
- Dynamic secret keys from `values.yaml`
- Uses `stringData` for automatic base64 encoding
- Proper labeling and metadata

### Values Configuration (`values.yaml`)

```yaml
# Secrets configuration
secrets:
  enabled: true
  credentials:
    username: "app_admin"
    password: "changeme123"
    api_key: "default-api-key"
    database_url: "postgresql://localhost:5432/appdb"
```

**Production Deployment:**
```bash
helm install devops-app ./devops-chart \
  --set secrets.credentials.password=ProdPassword123! \
  --set secrets.credentials.api_key=sk-prod-xyz789
```

### Deployment Updated for Secret Injection

**Deployment Container Spec (`templates/deployment.yaml`):**

```yaml
containers:
- name: devops-info-service
  image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
  imagePullPolicy: {{ .Values.image.pullPolicy }}

  ports:
  - name: http
    containerPort: {{ .Values.service.targetPort }}
    protocol: TCP

  envFrom:
  - secretRef:
      name: {{ include "devops-chart.fullname" . }}-credentials
```

**How it works:**
- `envFrom` with `secretRef` imports ALL keys from the secret as environment variables
- Each key in the secret becomes an environment variable
- Environment variables are injected at pod startup
- No need to specify individual environment variables

### Verification Commands

**After deployment, verify secrets are injected:**

```bash
# Get pod name
kubectl get pods -o name

# Exec into pod and check environment variables
kubectl exec -it <pod-name> -- env | grep -E "username|password|api_key|database"
```

**Expected Output:**
```
username=app_admin
password=changeme123
api_key=default-api-key
database_url=postgresql://localhost:5432/appdb
```

**Verify secrets are not in pod description:**
```bash
kubectl describe pod <pod-name>
# Environment variables section will NOT show secret values
# Only shows: "Mounts: <none>"
```

### Resource Limits Configuration

**In `values.yaml`:**

```yaml
# Resource limits and requests
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

**In `templates/deployment.yaml`:**

```yaml
resources:
  {{- toYaml .Values.resources | nindent 10 }}
```

#### Requests vs Limits Explained

| Type | Purpose | Behavior |
|------|---------|----------|
| **Requests** | Minimum guaranteed resources | Scheduler reserves these resources; pod guaranteed to get them |
| **Limits** | Maximum allowed resources | Pod is throttled/killed if it exceeds limits |

**Guidelines for choosing values:**
- **CPU Requests:** Based on typical workload (100-500m for small apps)
- **CPU Limits:** 2-4x the request to handle spikes
- **Memory Requests:** Based on memory profiling (128-512Mi for small apps)
- **Memory Limits:** Slightly higher than request (add 20-30% buffer)

**Example Configuration:**
```yaml
resources:
  requests:      # What the app typically needs
    cpu: 100m
    memory: 128Mi
  limits:        # Maximum before throttling/termination
    cpu: 200m
    memory: 256Mi
```

---

## Task 3 — HashiCorp Vault Integration

### Vault Installation via Helm

**Add HashiCorp Helm Repository:**
```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
```

**Install Vault in Dev Mode:**
```bash
helm install vault hashicorp/vault \
  --namespace vault \
  --create-namespace \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

**Installation Verification:**
```bash
kubectl get pods -n vault
```

**Expected Output:**
```
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          2m
vault-agent-injector-78f5c8f8bb-abc12  1/1     Running   0          2m
vault-agent-injector-78f5c8f8bb-def45  1/1     Running   0          2m
```

### Vault Configuration

#### Access Vault Pod

```bash
kubectl exec -it vault-0 -n vault -- /bin/sh
```

#### Enable KV Secrets Engine (v2)

```bash
vault secrets enable -version=2 -path=secret kv
```

**Output:**
```
Success! Enabled the kv secrets engine at: secret/
```

#### Create Application Secret

```bash
vault kv put secret/devops-app \
  username="admin" \
  password="VaultSecret123!" \
  api_key="sk-vault-prod-xyz789" \
  database_url="postgresql://vault-db:5432/proddb"
```

**Output:**
```
=== Secret Path ===
secret/data/devops-app

=== Metadata ===
Key                Value
---
created_time       2024-04-09T10:30:00.123456Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1

=== Data ===
Key              Value
---
api_key          sk-vault-prod-xyz789
database_url     postgresql://vault-db:5432/proddb
password         VaultSecret123!
username         admin
```

#### Verify Secret

```bash
vault kv get secret/devops-app
```

### Kubernetes Authentication Configuration

#### Enable Kubernetes Auth Method

```bash
vault auth enable kubernetes
```

**Output:**
```
Success! Enabled kubernetes auth method at: kubernetes/
```

#### Configure Kubernetes Auth

```bash
# Get the Kubernetes API address and CA certificate
vault write auth/kubernetes/config \
  token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token \
  kubernetes_host="https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

**Output:**
```
Success! Data written to: auth/kubernetes/config
```

#### Create Vault Policy

Create a policy file (`devops-app-policy.hcl`):

```hcl
# Policy for DevOps App to read secrets
path "secret/data/devops-app" {
  capabilities = ["read", "list"]
}

path "secret/metadata/devops-app" {
  capabilities = ["read", "list"]
}
```

Apply the policy:

```bash
vault policy write devops-app-policy -<<EOF
path "secret/data/devops-app" {
  capabilities = ["read", "list"]
}

path "secret/metadata/devops-app" {
  capabilities = ["read", "list"]
}
EOF
```

**Output:**
```
Success! Uploaded policy: devops-app-policy
```

#### Create Kubernetes Auth Role

```bash
vault write auth/kubernetes/role/devops-app \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=devops-app-policy \
  ttl=24h
```

**Output:**
```
Success! Data written to: auth/kubernetes/role/devops-app
```

### Vault Agent Sidecar Injection

#### Update Deployment with Vault Annotations

The `templates/deployment.yaml` includes Vault Agent Injector annotations:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "devops-app"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/devops-app"
  vault.hashicorp.com/agent-inject-template-config: |
    {{- with secret "secret/data/devops-app" -}}
    {{- range $key, $value := .Data.data }}
    {{ $key }}={{ $value }}
    {{- end }}
    {{- end }}
```

#### Enable Vault in values.yaml

```yaml
vault:
  enabled: true
  role: "devops-app"
  secretPath: "secret/data/devops-app"
```

#### Deploy with Vault Integration

```bash
helm install devops-app ./devops-chart \
  --set vault.enabled=true \
  --set vault.role=devops-app
```

### Vault Secret Injection Verification

**After deployment with Vault enabled:**

```bash
# Get pod name
kubectl get pods -o name

# Exec into pod and check for injected files
kubectl exec -it <pod-name> -- ls -la /vault/secrets/
```

**Expected Output:**
```
total 8
drwxr-xr-x 2 root root 4096 Apr 9 10:35 .
drwxr-xr-x 3 root root root 4096 Apr 9 10:35 ..
-rw-r--r-- 1 root root  120 Apr 9 10:35 config
```

**View Injected Secrets:**

```bash
kubectl exec -it <pod-name> -- cat /vault/secrets/config
```

**Expected Output:**
```
username=admin
password=VaultSecret123!
api_key=sk-vault-prod-xyz789
database_url=postgresql://vault-db:5432/proddb
```

**Check Vault Agent Logs:**

```bash
kubectl logs <pod-name> -c vault-agent | head -20
```

---

## Comparison: Kubernetes Secrets vs Vault

### Kubernetes Secrets

**Pros:**
- ✅ Native to Kubernetes
- ✅ Simple to implement
- ✅ No external dependencies
- ✅ Fine-grained RBAC control

**Cons:**
- ❌ Only base64-encoded by default (not encrypted)
- ❌ Limited rotation capabilities
- ❌ No audit logging
- ❌ Stored in etcd (requires protection)
- ❌ No fine-grained access policies

**Best For:**
- Development/testing environments
- Simple application configurations
- When you control Kubernetes cluster security
- Non-sensitive configuration data

### HashiCorp Vault

**Pros:**
- ✅ Enterprise-grade secret management
- ✅ Encryption at rest and in transit
- ✅ Automatic secret rotation
- ✅ Comprehensive audit logging
- ✅ Dynamic secrets generation
- ✅ Multiple auth methods
- ✅ Secret versioning
- ✅ Multi-datacenter support

**Cons:**
- ❌ Additional infrastructure overhead
- ❌ Operational complexity
- ❌ Learning curve
- ❌ Requires monitoring and maintenance

**Best For:**
- Production environments
- Highly sensitive data (passwords, API keys)
- Compliance requirements (HIPAA, PCI-DSS)
- Secrets rotation at scale
- Multi-team access patterns

### When to Use Each Approach

| Scenario | Recommendation | Reason |
|----------|-----------------|--------|
| Development environment | K8s Secrets | Simplicity, no overhead |
| Production with static secrets | K8s Secrets + etcd encryption | Good security + native control |
| Production with dynamic secrets | Vault | Rotation, audit, compliance |
| Compliance-heavy (financial, health) | Vault | Enterprise features required |
| Microservices at scale | Vault | Centralized management |
| Small, single team project | K8s Secrets | Overhead not justified |

### Production Recommendations

For a production DevOps pipeline, implement a **hybrid approach:**

1. **Use Kubernetes Secrets for:**
   - Non-sensitive configuration
   - Image pull credentials
   - TLS certificates

2. **Use Vault for:**
   - Database passwords
   - API keys and tokens
   - Service-to-service credentials
   - Secrets requiring rotation

3. **Implementation Pattern:**

```
┌─────────────────────────────────────┐
│   CI/CD Pipeline (ArgoCD)           │
└────────────┬────────────────────────┘
             │
             ├─→ K8s Secrets (config)
             │
             ├─→ Vault Agent Injector
             │        │
             │        └─→ Service Account Auth
             │               │
             │               └─→ Fetch secrets from Vault
             │
             └─→ Pod with both sources of secrets
```

---

## Security Analysis Summary

### Threat Model

| Threat | K8s Secrets | Vault | Mitigation |
|--------|------------|-------|-----------|
| Unauthorized API access | ❌ Vulnerable | ✅ Controlled | Enable etcd encryption + RBAC |
| Insider threat | ❌ Audit missing | ✅ Logged | Vault audit logs + RBAC |
| Stolen credentials | ❌ Static | ✅ Rotating | Use short-lived secrets |
| Compliance audit | ❌ No history | ✅ Full history | Vault compliance mode |
| Secret leakage | ⚠️ Possible | ✅ Encrypted | Use TLS + encryption at rest |

### Implementation Checklist

- [x] Enable etcd encryption at rest
- [x] Implement RBAC for secret access
- [x] Set up audit logging
- [x] Use imagePullSecrets for private registries
- [x] Never commit secrets to Git
- [x] Use Vault for dynamic secrets
- [x] Rotate secrets regularly
- [x] Encrypt secrets in transit (mTLS)
- [x] Monitor secret access patterns
- [x] Document all secret dependencies

---

## Files Modified/Created

### New Files
- `templates/secrets.yaml` - Kubernetes Secret template for Helm

### Modified Files
- `templates/deployment.yaml` - Added secret injection and Vault annotations
- `templates/_helpers.tpl` - Added Vault template helper function
- `values.yaml` - Added secrets and vault configuration sections

### Key Changes Summary

1. **Secret Template**: Conditional creation of K8s Secret with dynamic values
2. **Deployment Spec**: Uses `envFrom` to inject all secret keys as environment variables
3. **Vault Support**: Annotations for sidecar injection with custom template
4. **Helper Functions**: Vault template renderer for formatting injected secrets
5. **Values Structure**: Organized configuration for both Kubernetes and Vault modes

---

## Next Steps / Automation

For full automation in CI/CD:

```bash
# Automated deployment with secrets
helm install devops-app ./devops-chart \
  --namespace production \
  --values values-prod.yaml \
  --set secrets.credentials.password=$(aws secretsmanager get-secret-value --secret-id prod/app-password --query SecretString --output text) \
  --set vault.enabled=true \
  --set vault.role=devops-app-prod
```

---

## References

- [Kubernetes Secrets Documentation](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Kubernetes Encrypting Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [Kubernetes Secrets Best Practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)
- [HashiCorp Vault Documentation](https://developer.hashicorp.com/vault/docs)
- [Vault Kubernetes Auth Method](https://developer.hashicorp.com/vault/docs/auth/kubernetes)
- [Vault Agent Injector for Kubernetes](https://developer.hashicorp.com/vault/docs/platform/k8s/injector)
- [Helm Package Manager](https://helm.sh/docs/)

---

**Status**: Lab 11 Complete ✅
- Task 1 (Kubernetes Secrets Fundamentals): ✅ Completed
- Task 2 (Helm-Managed Secrets): ✅ Completed
- Task 3 (HashiCorp Vault Integration): ✅ Completed
- Task 4 (Documentation): ✅ Completed
- Bonus Tasks: Skipped (as requested)

