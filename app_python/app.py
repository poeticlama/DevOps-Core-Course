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
app_logger = logging.getLogger(__name__)

# Visits Counter with File-Based Persistence
VISITS_FILE = Path(os.getenv("VISITS_FILE_PATH", "/data/visits"))
visits_lock = threading.Lock()

def ensure_visits_directory():
    """Ensure the directory for visits file exists"""
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)

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

# Initialize visits file on startup
ensure_visits_directory()
current_visits = read_visits_count()
app_logger.info(f"Initialized visits counter: {current_visits}")

# App
app = FastAPI(
    title="DevOps Info Service",
    version="1.0.0",
    description="DevOps course info service"
)

# Define metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"]
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"]
)

devops_info_system_collection_seconds = Histogram(
    "devops_info_system_collection_seconds",
    "System info collection time"
)

# Log app startup
@app.on_event("startup")
async def startup_event():
    app_logger.info("DevOps Info Service starting up")


# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    app_logger.info(f"HTTP request: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")
    
    start_time = time.time()
    method = request.method
    endpoint = request.url.path

    # Filter out metrics endpoint if you don't want to track it, but we'll track it
    # We can normalize dynamic URLs here if needed

    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        raise e
    finally:
        duration = time.time() - start_time
        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
        http_requests_total.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

    app_logger.info(f"HTTP response: {request.method} {request.url.path} -> {response.status_code}")
    
    return response


# Config
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8080))

START_TIME = datetime.now(timezone.utc)


def get_uptime():
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return seconds, f"{hours} hours, {minutes} minutes"


@app.get("/")
async def index(request: Request):
    col_start = time.time()

    # Increment visits counter
    visits_count = increment_visits()

    uptime_seconds, uptime_human = get_uptime()
    system_info = {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "python_version": platform.python_version()
    }
    devops_info_system_collection_seconds.observe(time.time() - col_start)

    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI",
            "visits": visits_count
        },
        "system": system_info,
        "runtime": {
            "uptime_seconds": uptime_seconds,
            "uptime_human": uptime_human,
            "current_time": datetime.now(timezone.utc).isoformat(),
            "timezone": "UTC"
        },
        "request": {
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "method": request.method,
            "path": request.url.path
        },
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Service information"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/visits", "method": "GET", "description": "Get total visit count"},
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"}
        ]
    }

@app.get("/visits")
async def get_visits():
    """Return the current visits count"""
    visits_count = read_visits_count()
    app_logger.info(f"Visits endpoint accessed. Current count: {visits_count}")
    return {
        "visits": visits_count,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
async def health():
    uptime_seconds, _ = get_uptime()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds
    }


@app.exception_handler(404)
async def not_found(_, __):
    app_logger.warning("404 Not Found endpoint accessed")
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": "Endpoint does not exist"}
    )
