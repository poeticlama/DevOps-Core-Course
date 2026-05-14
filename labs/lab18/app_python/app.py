import os
import sys
import socket
import platform
import logging
import json
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
from pathlib import Path
import threading


# JSON Logging Formatter
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


# Configure JSON logging
def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO")
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add JSON handler to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    return root_logger



logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="DevOps Info Service",
    description="Service that provides DevOps related information",
    version="1.0.0"
)

# Prometheus Metrics
request_count = Counter(
    'app_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'app_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

app_info = Gauge(
    'app_info',
    'Application information',
    ['hostname', 'platform', 'python_version']
)

# Set app info
hostname = socket.gethostname()
app_info.labels(
    hostname=hostname,
    platform=platform.system(),
    python_version=platform.python_version()
).set(1)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Record metrics
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)

    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/")
async def root():
    """Root endpoint - returns basic service info"""
    return JSONResponse({
        "service": "DevOps Info Service",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.get("/info")
async def info():
    """Returns DevOps environment information"""
    info_data = {
        "hostname": socket.gethostname(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor() or "N/A"
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable
        },
        "network": {
            "fqdn": socket.getfqdn(),
            "ipv4": socket.gethostbyname(socket.gethostname())
        },
        "environment": {
            "user": os.getenv("USER") or os.getenv("USERNAME", "unknown"),
            "pwd": os.getcwd(),
            "path": os.getenv("PATH", "N/A")[:200]  # Limit length
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return JSONResponse(info_data)


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/echo")
async def echo(request: Request):
    """Echo endpoint - returns what was sent"""
    body = await request.json()
    return JSONResponse({
        "echo": body,
        "received_at": datetime.now(timezone.utc).isoformat()
    })


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

