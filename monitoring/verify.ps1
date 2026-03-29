# Lab 7 Verification Script (Windows PowerShell)
# Checks that all components are working correctly

Write-Host "=== Lab 7 - Loki Stack Verification ===" -ForegroundColor Cyan
Write-Host ""

function Check-Service {
    param (
        [string]$name,
        [int]$port,
        [string]$endpoint = ""
    )

    Write-Host -NoNewline "Checking $name... "
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$port$endpoint" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✓" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "✗" -ForegroundColor Red
        return $false
    }
}

# Check services
Write-Host "1. Checking Services" -ForegroundColor Yellow
Check-Service "Loki" 3100 "/ready"
Check-Service "Grafana" 3000 "/api/health"
Check-Service "App" 8000 "/health"

Write-Host ""
Write-Host "2. Checking Docker Containers" -ForegroundColor Yellow
docker compose ps

Write-Host ""
Write-Host "3. Verifying Promtail Scraping" -ForegroundColor Yellow
Write-Host "Promtail targets:"
try {
    $targets = Invoke-WebRequest -Uri "http://localhost:9080/targets" -UseBasicParsing | ConvertFrom-Json
    $targets | ConvertTo-Json | Write-Host
} catch {
    Write-Host "Could not fetch targets"
}

Write-Host ""
Write-Host "4. Generate Test Traffic" -ForegroundColor Yellow
Write-Host "Making 10 requests to app..."
for ($i = 1; $i -le 10; $i++) {
    Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue | Out-Null
    Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue | Out-Null
}
Write-Host "Done"

Write-Host ""
Write-Host "5. Checking Application Logs" -ForegroundColor Yellow
Write-Host "Recent app logs:"
docker compose logs app-python --tail 3

Write-Host ""
Write-Host "=== Verification Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Open Grafana: http://localhost:3000"
Write-Host "2. Add Loki data source: http://loki:3100"
Write-Host "3. Query in Explore: {app=`"devops-python`"}"
Write-Host "4. View Dashboard: Dashboards → Lab 7 - Loki Logs Dashboard"
Write-Host ""

