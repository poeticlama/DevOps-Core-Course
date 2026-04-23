# DevOps Info Service (Python)

[![Python CI](https://github.com/YOUR_USERNAME/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/DevOps-Core-Course/actions/workflows/python-ci.yml)

A simple web service that provides information about the application itself,
the runtime environment, and system health.  
This project is part of **Lab 1** of the DevOps Core Course.

## Overview

The service exposes the following HTTP endpoints:

- `/` — returns detailed service, system, runtime, and request information (increments visits counter)
- `/health` — returns a basic health status for monitoring
- `/visits` — returns the current visit count
- `/metrics` — returns Prometheus metrics

The application is built with **FastAPI** and follows Python best practices.

### Persistent Storage

The application implements a visits counter that persists across restarts:
- Counter is stored in a file (default: `/data/visits`)
- Uses thread-safe file operations with locking
- Persists across container restarts when volume is mounted

### Environment Variables

- `LOG_LEVEL` — Logging level (default: `INFO`)
- `VISITS_FILE_PATH` — Path to visits counter file (default: `/data/visits`)
- `PORT` — Port number (default: `8080`)
- `HOST` — Host address (default: `127.0.0.1`)

## Prerequisites

- Python **3.11+**
- pip
- virtualenv (recommended)

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the application

```bash
python app.py
```

Custom configurations via env variables

```
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
```

## Testing

The application includes comprehensive unit tests using **pytest**.

### Run all tests

```bash
pytest -v
```

### Run with coverage

```bash
pytest --cov=app --cov-report=term-missing
```

### Run specific test class

```bash
pytest tests/test_app.py::TestMainEndpoint -v
```

**Test Coverage:**
- ✅ All HTTP endpoints (`/`, `/health`)
- ✅ Response structure validation
- ✅ Error handling (404, 405)
- ✅ Time-dependent behavior
- ✅ 24 test cases, 100% pass rate

For detailed testing documentation, see [docs/LAB03-TASK1.md](docs/LAB03-TASK1.md).

## Docker

### Run with docker-compose (with persistence)

```bash
docker-compose up -d
```

This automatically creates a `./data` volume for visits counter persistence.

**Verify persistence:**
```bash
# Check visits count
curl http://localhost:8080/visits

# Check the file on host
cat ./data/visits

# Restart the container
docker-compose restart

# Verify counter continues from previous value
curl http://localhost:8080/visits
```

### Build image

```bash
docker build -t poeticlama/devops-info-service:latest .
```

### Run container

```bash
docker run -p 8080:8080 -v ./data:/data poeticlama/devops-info-service:latest
```

### Pull from Docker Hub

```bash
docker pull poeticlama/devops-info-service:latest
```
