#!/bin/bash
# Lab 7 Verification Script
# Checks that all components are working correctly

echo "=== Lab 7 - Loki Stack Verification ==="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local port=$2
    local endpoint=$3

    echo -n "Checking $name... "
    if curl -s "http://localhost:$port$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# Check services
echo "1. Checking Services"
check_service "Loki" 3100 "/ready"
check_service "Grafana" 3000 "/api/health"
check_service "App" 8000 "/health"

echo ""
echo "2. Checking Docker Containers"
docker compose ps

echo ""
echo "3. Verifying Promtail Scraping"
echo "Promtail targets:"
curl -s http://localhost:9080/targets | jq . 2>/dev/null || echo "Could not fetch targets"

echo ""
echo "4. Testing Loki Query"
echo "Querying logs from last 1 hour..."
curl -s 'http://localhost:3100/loki/api/v1/query_range?query={job="docker"}&start=1h-ago' | jq '.data.result | length' 2>/dev/null || echo "Could not query logs"

echo ""
echo "5. Generate Test Traffic"
echo "Making 10 requests to app..."
for i in {1..10}; do
    curl -s http://localhost:8000/ > /dev/null
    curl -s http://localhost:8000/health > /dev/null
done
echo "Done"

echo ""
echo "6. Checking Logs in Loki"
sleep 2  # Wait for logs to be ingested
echo "Logs containing 'HTTP':"
curl -s 'http://localhost:3100/loki/api/v1/query_range?query={app="devops-python"}|="HTTP"&start=10m-ago&limit=10' | jq '.data.result[0].values | length' 2>/dev/null || echo "Checking..."

echo ""
echo "=== Verification Complete ==="
echo ""
echo "Next steps:"
echo "1. Open Grafana: http://localhost:3000"
echo "2. Add Loki data source: http://loki:3100"
echo "3. Query in Explore: {app=\"devops-python\"}"
echo "4. View Dashboard: Dashboards → Lab 7 - Loki Logs Dashboard"
echo ""

