# Lab 7 — Observability & Logging with Loki Stack

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Network: logging                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │   Promtail   │────────▶│    Loki      │                     │
│  │ (Log Agent)  │         │(Log Storage) │                     │
│  └──────────────┘         └──────┬───────┘                     │
│         ▲                        │                              │
│         │                        │                              │
│    ┌────┴──────┬───────────┬────▼─────┐                        │
│    │            │           │          │                        │
│  ┌─┴──┐  ┌─────┴──┐  ┌───┴──┐  ┌───┴──┐                        │
│  │App │  │Grafana │  │ Root │  │Promtail                       │
│  │ 1  │  │(Viz)   │  │Host  │  │Metrics                        │
│  └─┬──┘  └────────┘  │Logs  │  └───────┘                       │
│    │                 │      │                                   │
│    └─────────────────┼──────┘                                   │
│      Logs (stdout)   │                                          │
│                      │                                          │
└─────────────────────────────────────────────────────────────────┘

Flow: Applications (stdout) → Docker Logs → Promtail → Loki ← Grafana
```

## Setup & Deployment Guide

### Prerequisites
- Docker Engine 20.10+ with Docker Compose v2
- Python 3.8+
- 2GB RAM available
- Ports available: 3000 (Grafana), 3100 (Loki), 8000 (App)

### 1. Deploy Loki Stack

```bash
cd monitoring/
docker compose up -d
```

Verify services are healthy:
```bash
docker compose ps
# All should show "Up" status with health checks

# Test Loki readiness
curl http://localhost:3100/ready
# Expected: 200 OK

# Check Promtail targets
curl http://localhost:9080/targets
```

### 2. Configure Grafana Data Source

1. Open http://localhost:3000
2. Login with admin/admin
3. **Connections** → **Data Sources** → **Add data source**
4. Select **Loki**
5. URL: `http://loki:3100`
6. Click **Save & Test**

### 3. Start Querying Logs

In Grafana **Explore** tab:
- Data source: **Loki**
- Query: `{job="docker"}`
- Click **Run query**

## Configuration Details

### Loki Configuration (`loki/config.yml`)

**Key sections:**

```yaml
auth_enabled: false
# No authentication (dev only, secure for production)

server:
  http_listen_port: 3100
  # Loki listens on port 3100

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      # TSDB = Time Series Database (Loki 3.0+)
      # 10x faster queries than previous versions
      # Better compression
      schema: v13
      # Schema version 13 required for TSDB

storage_config:
  filesystem:
    directory: /loki/chunks
    # Data stored in mounted volume

limits_config:
  retention_period: 168h
  # Keep logs for 7 days, then delete
```

**Why these choices:**
- **TSDB**: Modern Loki 3.0 default, much faster for metric queries
- **Filesystem storage**: Fine for single-node setups, easy to backup
- **7-day retention**: Balances storage costs with debugging access

### Promtail Configuration (`promtail/config.yml`)

**Key sections:**

```yaml
clients:
  - url: http://loki:3100/loki/api/v1/push
  # Where to send logs

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
    # Discovers containers automatically
```

**Label extraction** (in relabel_configs):
- Extracts `container` name from `__meta_docker_container_name`
- Extracts `app` label if container has `app=` label
- Extracts `image` and `tag` for debugging

**Why Docker SD?**
- Automatic container discovery
- No manual configuration needed
- Labels flow naturally into log queries

## Application Logging Implementation

### JSON Structured Logging

Updated `app.py` with:

```python
import json
import logging
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON logs"""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        return json.dumps(log_obj)
```

**What we log:**
- Application startup
- HTTP requests (method, path, client IP)
- HTTP responses (status code)
- Errors and exceptions

**Example log output:**
```json
{
  "timestamp": "2026-03-29T20:21:59.589742+00:00",
  "level": "INFO",
  "logger": "app",
  "message": "DevOps Info Service starting up",
  "module": "app",
  "function": "startup_event",
  "line": 60
}
```

**Benefits:**
- Parseable by log aggregation tools
- Easy to filter by field (e.g., `level="ERROR"`)
- Consistent format across microservices
- No information loss from text parsing

## Dashboard Walkthrough

### Panel 1: Recent Logs (Logs Table)

**Query:** `{app=~"devops-.*"}`

Shows all logs from apps matching pattern `devops-*`. Newest first.

**Use case:** Debugging current issues, following app behavior in real-time

### Panel 2: Request Rate (Time Series Graph)

**Query:** `sum by (app) (rate({app=~"devops-.*"} [1m]))`

Calculates logs per second by app over 1-minute windows.

**Explanation:**
- `{app=~"devops-.*"}` - Select logs from apps
- `rate(...[1m])` - Calculate rate over 1-minute intervals
- `sum by (app)` - Group results by app label

**Use case:** Detect traffic spikes or drops

### Panel 3: Error Logs (Logs Visualization)

**Query:** `{app=~"devops-.*"} | json | level="ERROR"`

Filters to only ERROR-level logs after parsing JSON.

**Explanation:**
- `| json` - Parse JSON structure
- `level="ERROR"` - Filter by level field

**Use case:** Alert monitoring, troubleshooting issues

### Panel 4: Log Level Distribution (Pie/Bar Chart)

**Query:** `sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))`

Counts total logs per level over 5-minute window.

**Explanation:**
- `count_over_time(...[5m])` - Count logs in 5-minute buckets
- `sum by (level)` - Group and sum by level field

**Use case:** Monitor log health (too many errors?), baseline expectations

## Production Configuration

### Security Hardening

#### 1. Disable Anonymous Access (Grafana)

```yaml
# docker-compose.yml
environment:
  - GF_AUTH_ANONYMOUS_ENABLED=false
  - GF_SECURITY_ADMIN_PASSWORD=secure_password_here
```

**Why:** Prevents unauthorized access to dashboards and data sources

#### 2. Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

**Prevents:** Runaway containers consuming all system resources

#### 3. Health Checks

```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:3100/ready || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

**Benefits:** Docker restarts unhealthy services automatically

### Retention Policy

Current setting: 7 days (168h)

**Adjust based on:**
- Storage availability (each GB ~= days of logs)
- Compliance requirements (audits may require longer retention)
- Cost considerations

For longer retention (e.g., 30 days):
```yaml
limits_config:
  retention_period: 720h  # 30 days
```

## Testing & Verification

### 1. Generate Test Logs

```bash
# Generate traffic to app
for i in {1..20}; do 
  curl http://localhost:8000/
  curl http://localhost:8000/health
done
```

### 2. Verify in Grafana

**Query 1: All logs**
```logql
{job="docker"}
```
Expected: Logs from loki, promtail, grafana, app-python containers

**Query 2: App-only logs**
```logql
{app="devops-python"}
```
Expected: JSON logs with timestamps, levels, messages

**Query 3: HTTP requests**
```logql
{app="devops-python"} |= "HTTP request"
```
Expected: Request logs with method, path, client IP

**Query 4: Response logs**
```logql
{app="devops-python"} |= "HTTP response"
```
Expected: Response logs with status codes

**Query 5: Error filter**
```logql
{app="devops-python"} | json | level="ERROR"
```
Expected: Only error-level logs (may be empty initially)

### 3. Verify Health

```bash
# Loki ready check
curl -I http://localhost:3100/ready
# HTTP/1.1 200 OK

# Grafana API
curl -s http://localhost:3000/api/health | jq .
# {database: ok, ok: true}

# Promtail targets
curl -s http://localhost:9080/targets | jq .
```

## Challenges & Solutions

### Challenge 1: Promtail Can't Reach Loki

**Symptom:** Promtail logs show "server misbehaving"

**Solution:**
- Verify both containers are on same network: `docker network ls`
- Check DNS works: `docker exec promtail ping loki`
- Verify Loki is actually listening: `docker logs loki | grep "listening"`

### Challenge 2: No Logs Appearing in Grafana

**Symptom:** Query returns empty results

**Possible causes:**
- Loki data source not connected: Verify in Grafana datasource settings
- No containers labeled for scraping: Add `labels: {logging: "promtail"}` to containers
- Container startup before Promtail ready: Restart Promtail with `docker compose restart promtail`

**Debug:**
```bash
# Check Promtail is scraping
docker logs promtail | grep "added Docker target"

# Check container labels
docker inspect <container-id> | grep -A 5 "Labels"
```

### Challenge 3: Dashboard Queries Not Working

**Symptom:** Query returns error or no data

**Check:**
- Data source is set to Loki (top-left dropdown)
- Query syntax is valid LogQL
- Labels match actual container labels (case-sensitive!)
- Time range isn't in the past (check dashboard time picker)

### Challenge 4: High Memory Usage

**Symptom:** Docker reports OOMKilled containers

**Solution:**
- Increase memory limits in docker-compose.yml
- Reduce retention period (fewer logs to store)
- Enable log compression (Loki 3.0 does this automatically)

## Deployment Checklist

- [x] Docker Compose file with all 4 services
- [x] Loki config with TSDB storage
- [x] Promtail config with Docker SD
- [x] Python app updated with JSON logging
- [x] App added to docker-compose.yml
- [x] Health checks on all services
- [x] Resource limits defined
- [x] Grafana secured (no anonymous access)
- [x] Loki data source provisioned
- [x] Dashboard with 4 panels created
- [x] Test queries documented
- [x] All logs visible in Grafana

## References

- [Loki 3.0 Documentation](https://grafana.com/docs/loki/latest/)
- [LogQL Query Language](https://grafana.com/docs/loki/latest/query/)
- [Promtail Configuration](https://grafana.com/docs/loki/latest/send-data/promtail/configuration/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## Next Steps

1. Integrate with existing Prometheus for metrics (Lab 8)
2. Deploy to Kubernetes with Helm (Labs 9-12)
3. Set up alerting rules in Loki/AlertManager
4. Implement multi-tenant logging
5. Add log sampling for high-volume services

