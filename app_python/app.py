import os
import sys
import socket
import platform
import logging
import json
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


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

# App
app = FastAPI(
    title="DevOps Info Service",
    version="1.0.0",
    description="DevOps course info service"
)

# Log app startup
@app.on_event("startup")
async def startup_event():
    app_logger.info("DevOps Info Service starting up")


# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    app_logger.info(f"HTTP request: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")
    
    response = await call_next(request)
    
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
    uptime_seconds, uptime_human = get_uptime()

    return {
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI"
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version()
        },
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
            {"path": "/health", "method": "GET", "description": "Health check"}
        ]
    }


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

