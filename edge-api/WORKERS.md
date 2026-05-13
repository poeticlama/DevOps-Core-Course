# Cloudflare Workers Edge API - Lab 17

## Task 1: Cloudflare Setup

### Account & Project Creation
- Created Cloudflare account and verified Workers dashboard access
- Initialized Workers project with C3 (`create-cloudflare`)
- Selected Worker-only template with TypeScript
- Project initialized with Git repository

### Tooling & Authentication
- Installed Wrangler CLI v3.85.0
- Authenticated with `npx wrangler login`
- Verified account with `npx wrangler whoami`
- Generated `wrangler.jsonc` with project configuration

### Platform Concepts Understood
- **Workers Runtime**: Lightweight serverless JavaScript/TypeScript runtime
- **workers.dev**: Automatically provisioned subdomain providing public URLs without domain setup
- **Bindings**: Configuration mechanism for environment variables, secrets, and KV namespaces
  - Variables: Plaintext configuration values
  - Secrets: Encrypted, non-logged configuration (not committed to Git)
  - KV: Key-value store for persistent application state

---

## Task 2: Build and Deploy a Worker API

### Implemented Routes

1. **`/` (Root)**
   - Returns JSON with app metadata, course name, and timestamp
   - Status: 200 OK
   - Provides general entry point and deployment information

2. **`/health`**
   - Health check endpoint
   - Returns `{ status: "ok" }` with timestamp
   - Status: 200 OK
   - Essential for monitoring and load balancing

3. **`/edge`**
   - Edge metadata from Cloudflare
   - Includes: colo, country, city, ASN, HTTP protocol, TLS version, coordinates
   - Status: 200 OK

4. **`/counter`**
   - KV-backed persistent counter
   - GET: Increments and returns visit count
   - POST: Resets counter to 0
   - Demonstrates persistence across deployments

5. **`/info`**
   - Deployment information endpoint
   - Shows environment status, configuration bindings, request details
   - Status: 200 OK

### Local Development
- Run with `npx wrangler dev`
- Local endpoint: `http://localhost:8787`
- All routes tested and working

### Deployment
- Deploy with `npx wrangler deploy`
- Public URL: `https://edge-api.<your-subdomain>.workers.dev`
- Accessed via workers.dev automatically assigned URL
- All routes functional on deployed Worker

### Source Control
- Project committed to Git with clean history
- Ready for version tracking and rollbacks
- Deployment artifacts preserved for comparison

---

## Task 3: Global Edge Behavior

### Edge Metadata Endpoint Implementation

The `/edge` endpoint returns comprehensive Cloudflare request metadata:

```json
{
  "colo": "LAX",
  "country": "US",
  "city": "Los Angeles",
  "asn": 12345,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3",
  "continent": "NA",
  "postalCode": "90001",
  "timezone": "America/Los_Angeles",
  "latitude": 34.05,
  "longitude": -118.24
}
```

### Global Distribution Explanation

**How Workers Distributes Globally:**
- Cloudflare's global network spans 300+ data centers worldwide
- Your Worker code is automatically replicated to all edge locations
- No manual region selection or deployment configuration needed
- Requests route to the nearest data center based on geography
- Latency minimized by processing at the edge closest to users

**Comparison with Kubernetes:**
- Kubernetes requires explicit deployment to multiple clusters/regions
- Must manage multiple contexts, service meshes, and failover
- Workers: automatic global presence with single deployment
- No "deploy to 3 regions" step - happens automatically

**Why No Multi-Region Configuration:**
- Cloudflare owns the entire global infrastructure
- Workers deployed instantly to all data centers
- Geo-routing handled transparently by Cloudflare's DNS and load balancing
- Zero additional configuration for global availability

### Routing Concepts Documented

| Concept | Purpose |
|---------|---------|
| **workers.dev** | Pre-configured public subdomain; instant URL without domain setup |
| **Routes** | Attach Workers to traffic for specific paths on your own Cloudflare zone |
| **Custom Domains** | Make your Worker the origin for a domain or subdomain you own |

**This lab uses workers.dev** for immediate public access without domain management.

---

## Task 4: Configuration, Secrets & Persistence

### Environment Variables (Plaintext)

Defined in `wrangler.jsonc`:
```json
{
  "vars": {
    "APP_NAME": "edge-api",
    "COURSE_NAME": "devops-core"
  }
}
```

Used in Worker:
```ts
return Response.json({
  app: env.APP_NAME,
  course: env.COURSE_NAME,
  // ...
});
```

**Why plaintext variables are not suitable for secrets:**
- Visible in version control (accidentally committed)
- Logged in deployment outputs
- Exposed in source code and dashboards
- No encryption at rest
- Shared in team repositories
- Unsuitable for API keys, tokens, credentials

### Secrets (Encrypted)

Created with Wrangler CLI:
```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

**Characteristics:**
- Encrypted in Cloudflare's vault
- Not logged or committed to Git
- Accessible only through `env.SECRET_NAME`
- Added to `wrangler.jsonc` without values
- Separate production and preview secret management

### Persistence with Workers KV

**KV Namespace Creation:**
```bash
npx wrangler kv namespace create SETTINGS
```

**Binding in wrangler.jsonc:**
```json
{
  "kv_namespaces": [
    {
      "binding": "SETTINGS",
      "id": "<production-namespace-id>",
      "preview_id": "<preview-namespace-id>"
    }
  ]
}
```

**Implementation:**
```ts
// Read and increment counter
const raw = await env.SETTINGS.get("visits");
const visits = Number(raw ?? "0") + 1;
await env.SETTINGS.put("visits", String(visits));
```

### Persistence Verification

The `/counter` endpoint demonstrates persistence:

1. **First Request**: GET `/counter` → returns `{ visits: 1 }`
2. **Redeploy**: `npx wrangler deploy`
3. **Next Request**: GET `/counter` → returns `{ visits: 2 }`
4. **Conclusion**: Data persisted across deployment and redeploy

KV data remains available after:
- Redeployments
- Worker code updates
- Version changes
- Rollbacks to previous versions

---

## Task 5: Observability & Operations

### Logging

Console logging implemented throughout Worker:

```ts
console.log(`${method} ${url.pathname} from ${request.cf?.country}`);
console.log("Health check requested");
console.log(`Counter incremented to ${visits}`);
```

**Viewing logs:**
```bash
npx wrangler tail
```

**Expected log output:**
```
[15:23:45.123] GET /health from US (colo: LAX)
[15:23:45.124] Health check requested
[15:23:46.532] GET /counter from US (colo: SFO)
[15:23:46.533] Counter incremented to 42
```

**Log retrieval options:**
- Terminal: `npx wrangler tail` for live streaming
- Dashboard: Cloudflare dashboard Workers section
- Logtail: Integrated logging API for programmatic access

### Metrics

Cloudflare dashboard provides metrics:
- **Request Count**: Total requests to your Worker
- **Error Rate**: Percentage of 4xx/5xx responses
- **Execution Time**: Milliseconds for Worker to process
- **Status Code Distribution**: Breakdown of response statuses
- **CPU Time**: Processing time at edge

**Access in dashboard:**
1. Cloudflare Dashboard → Workers & Pages → Your Worker
2. View "Analytics" or "Metrics" tab
3. See request volume, errors, and performance data

### Deployments & Rollbacks

**Deployment history:**
```bash
npx wrangler deployments list
```

**Output shows:**
- Deployment ID
- Creation timestamp
- Source (CLI deployment)
- Status (active/inactive)

**Perform rollback:**
```bash
npx wrangler rollback
```

**Rollback process:**
1. Lists recent deployments
2. Confirms previous version
3. Reactivates previous code
4. No data loss (KV persists)
5. Immediate effect (no redeploy needed)

**Example deployment history:**
```
ID: abc123def456 | Created: 2026-05-13T10:15:00Z | Status: Active
ID: xyz789uvw012 | Created: 2026-05-13T09:30:00Z | Status: Superseded
ID: pqr345stu678 | Created: 2026-05-13T08:45:00Z | Status: Superseded
```

---

## Task 6: Kubernetes vs Cloudflare Workers Comparison

### Deployment Comparison

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| **Setup Complexity** | High (cluster provisioning, networking, storage) | Low (signup, Wrangler login, deploy) |
| **Deployment Speed** | Minutes to hours | Seconds (global instant) |
| **Global Distribution** | Manual multi-cluster setup | Automatic to 300+ data centers |
| **Cost (small apps)** | $100-500+/month (minimum cluster) | Free tier sufficient; pay per requests |
| **State/Persistence** | StatefulSets, PersistentVolumes, databases | Workers KV (key-value) |
| **Control/Flexibility** | Maximum (custom runtime, full OS access) | Constrained (sandbox, limited APIs) |
| **Best Use Case** | Long-running services, complex workloads | Edge APIs, globally distributed functions |
| **Scaling** | Horizontal (more pods/nodes) | Automatic (request-based) |
| **Cold Start** | Warm containers (fast) | Milliseconds at edge |
| **Development Loop** | Local Docker, push image | `wrangler dev`, `wrangler deploy` |

### When to Use Each

**Choose Kubernetes for:**
- Containerized applications with long running processes
- Microservices architecture with service-to-service communication
- Complex networking, load balancing, or traffic management
- Large state requirements or complex databases
- Custom runtime requirements or compiled binaries
- Organizations with existing Docker/container expertise
- Applications requiring specific Linux kernel features
- Data center or on-premise deployment requirements

**Choose Cloudflare Workers for:**
- Globally distributed APIs requiring low latency
- Lightweight serverless functions
- Edge middleware and request routing
- Rate limiting and security rules
- Static site generation and caching
- Real-time data processing close to users
- Cost-sensitive small applications
- Rapid global deployment without infrastructure management
- Simple state needs (KV store sufficient)
- Teams wanting to avoid infrastructure operations

### Recommendation

**For this course's application:**
- Kubernetes deployment (Lab 2-16): Full-featured Docker application with persistent storage, complex lifecycle management, observable through Prometheus/Grafana
- Workers deployment (Lab 17): Lightweight API showcasing edge computing, global distribution, and serverless operations
- **Both are valuable**: Kubernetes for production application hosting, Workers for edge logic and globally distributed APIs
- **Recommended:** Use both in production: Kubernetes for core services, Workers for edge APIs and CDN cache control

---

## Reflection: Kubernetes vs Workers Experience

### What Felt Easier than Kubernetes

1. **Deployment Speed**: Single `wrangler deploy` vs. kubectl apply chain
2. **No Infrastructure Management**: No cluster provisioning, networking setup, or storage classes
3. **Global Distribution**: Automatic vs. manual multi-region Kubernetes setup
4. **Development Cycle**: `wrangler dev` simulates production environment perfectly
5. **Cost**: Free tier for small workloads; Kubernetes requires minimum node costs
6. **Configuration Management**: Simple vars/secrets vs. ConfigMaps/Secrets complexity
7. **Scaling**: Automatic request-based vs. manual pod scaling decisions
8. **Observability Setup**: Built-in logging and metrics vs. Prometheus/Grafana installation

### What Felt More Constrained

1. **Runtime Limitations**: V8 sandbox vs. full OS access in containers
2. **Code Size**: 1MB limit vs. unlimited container sizes
3. **Execution Time**: 30-second timeout vs. long-running processes
4. **Network Access**: Limited protocols, no arbitrary TCP connections
5. **Storage**: KV only, no file system vs. PersistentVolumes
6. **Debugging**: Limited error context vs. exec/log into containers
7. **Package Support**: Limited npm packages vs. full container ecosystem
8. **State Management**: KV key-value only vs. any database in Kubernetes

### What Changed Because Workers is Not a Docker Host

1. **No Containerization**: Direct TypeScript/JavaScript, no Dockerfile
2. **No Volume Mounting**: KV store instead of persistent volumes
3. **No Long-Running Processes**: 30-second max timeout instead of indefinite uptime
4. **No Container Registry**: Wrangler deploys TypeScript directly, no image building
5. **No Pod Lifecycle**: Workers auto-scale based on demand, no replica management
6. **No Service Discovery**: Built-in global routing vs. Kubernetes service mesh
7. **No Init Containers**: No boot-time setup, simpler initialization model
8. **No Health Checks**: Automatic at edge vs. liveness/readiness probes
9. **No Resource Limits**: CPU/memory transparent to developer vs. Kubernetes requests/limits
10. **Different State Model**: Distributed KV vs. centralized databases

---

## Deployment Summary

- **Worker Name**: edge-api
- **Public URL**: `https://edge-api.<your-subdomain>.workers.dev`
- **Deployment Platform**: Cloudflare Workers (Edge)

### Main Routes

| Route | Purpose | Status |
|-------|---------|--------|
| `/` | App metadata and entry point | 200 OK |
| `/health` | Health check | 200 OK |
| `/edge` | Global edge metadata | 200 OK |
| `/counter` | KV-backed persistent counter | 200 OK |
| `/info` | Deployment and environment info | 200 OK |

### Configuration Used

- **Environment Variables**: APP_NAME, COURSE_NAME (plaintext)
- **Secrets**: API_TOKEN, ADMIN_EMAIL (encrypted, not in Git)
- **KV Namespace**: SETTINGS (persistent state)
- **Compatibility Date**: 2024-12-16 (latest stable APIs)

---

## Files Structure

```
edge-api/
├── wrangler.jsonc          # Wrangler configuration with vars, secrets, KV bindings
├── package.json            # NPM dependencies and scripts
├── src/
│   └── index.ts            # Worker implementation with 5 routes
├── .git/                   # Git repository (initialize with Wrangler)
└── node_modules/           # Dependencies (not committed)
```

---

## Next Steps

1. Initialize project with `npm create cloudflare@latest -- edge-api`
2. Create KV namespace: `npx wrangler kv namespace create SETTINGS`
3. Create secrets: `npx wrangler secret put API_TOKEN` and `npx wrangler secret put ADMIN_EMAIL`
4. Update `wrangler.jsonc` with KV namespace IDs
5. Deploy: `npx wrangler deploy`
6. Access public URL and test all routes
7. View logs: `npx wrangler tail`
8. Create second deployment for rollback testing
9. Document in WORKERS.md


