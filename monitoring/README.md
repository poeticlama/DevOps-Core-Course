# Monitoring Stack - Loki, Promtail, Grafana

Centralized logging solution for containerized applications using the Grafana Loki stack.

## Quick Start

```bash
# Deploy the stack
docker compose up -d

# Verify services
docker compose ps

# Test Loki
curl http://localhost:3100/ready

# Access Grafana
open http://localhost:3000
# Login: admin / admin
```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| **Loki** | 3100 | Log storage and querying (TSDB) |
| **Promtail** | 9080 | Log collection from Docker |
| **Grafana** | 3000 | Visualization and dashboarding |
| **App-Python** | 8000 | Application with JSON logging |

## Directory Structure

```
monitoring/
├── docker-compose.yml              # Service definitions
├── loki/
│   └── config.yml                 # Loki configuration
├── promtail/
│   └── config.yml                 # Promtail configuration
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── loki.yaml         # Loki data source provisioning
│   │   └── dashboards/
│   │       ├── dashboard-provider.yaml
│   │       └── lab07-dashboard.json  # Main dashboard
│   └── provisioning/               # Grafana configs
└── docs/
    └── LAB07.md                   # Complete documentation
```

## Configuration

### Loki
- **Storage**: TSDB with filesystem backend
- **Retention**: 7 days (168h)
- **Schema**: v13 (optimized for Loki 3.0+)

### Promtail
- **Collection**: Docker container logs via Unix socket
- **Service Discovery**: Automatic Docker SD
- **Push Target**: Loki at `http://loki:3100/loki/api/v1/push`

### Applications
- **Python App**: Logs in JSON format to stdout
- **Log Fields**: timestamp, level, message, module, function, line
- **Integration**: Automatic via Docker log driver

## Usage

### Query Logs in Grafana

1. Open http://localhost:3000
2. Go to **Explore** tab
3. Select **Loki** data source
4. Try these queries:

```logql
# All logs
{job="docker"}

# App-only logs
{app="devops-python"}

# HTTP requests
{app="devops-python"} |= "HTTP request"

# Errors only
{app="devops-python"} | json | level="ERROR"

# Rate of logs per second
rate({app="devops-python"}[1m])
```

### View Dashboard

1. Click **Dashboards** in left sidebar
2. Select **Lab 7 - Loki Logs Dashboard**
3. 4 panels show:
   - Recent logs table
   - Request rate graph
   - Log level distribution pie chart
   - Error logs table

## Troubleshooting

### Services won't start
```bash
# Check logs
docker compose logs

# Rebuild from scratch
docker compose down -v
docker compose up -d
```

### No logs in Grafana
```bash
# Verify Promtail is scraping
docker logs promtail | grep "added Docker target"

# Check container labels
docker inspect <container-id> | grep Labels

# Verify data source connection
curl http://loki:3100/ready
```

### High memory usage
- Reduce retention period in `loki/config.yml`
- Increase memory limits in `docker-compose.yml`
- Reduce number of scrape configs in Promtail

## Production Considerations

1. **Authentication**: Set `GF_AUTH_ANONYMOUS_ENABLED=false` in docker-compose.yml
2. **Storage**: Use object storage (S3, GCS) instead of filesystem for scale
3. **Retention**: Adjust based on compliance requirements
4. **Backups**: Volume backups for Grafana dashboards and Loki data
5. **Monitoring**: Monitor Loki itself with Prometheus
6. **Alerting**: Set up alert rules in Grafana for critical conditions

## Related Labs

- **Lab 1-4**: Application development and containerization
- **Lab 5-6**: Ansible and Docker Compose orchestration
- **Lab 8**: Metrics collection with Prometheus
- **Lab 9+**: Kubernetes deployment

## Resources

- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [LogQL Reference](https://grafana.com/docs/loki/latest/query/)
- [Promtail Configuration](https://grafana.com/docs/loki/latest/send-data/promtail/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)

## Support

For issues or questions, see `docs/LAB07.md` for detailed troubleshooting and architecture information.

