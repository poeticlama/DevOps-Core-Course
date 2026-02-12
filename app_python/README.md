# DevOps Info Service (Python)

[![Python CI](https://github.com/YOUR_USERNAME/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/DevOps-Core-Course/actions/workflows/python-ci.yml)

A simple web service that provides information about the application itself,
the runtime environment, and system health.  
This project is part of **Lab 1** of the DevOps Core Course.

## Overview

The service exposes two HTTP endpoints:

- `/` — returns detailed service, system, runtime, and request information
- `/health` — returns a basic health status for monitoring

The application is built with **FastAPI** and follows Python best practices.

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

### Build image

```bash
docker build -t poeticlama/devops-info-service:1.0 .
```

### Run container

```bash
docker run -p 8080:8080 poeticlama/devops-info-service:1.0
```

### Pull from Docker Hub

```bash
docker pull poeticlama/devops-info-service:1.0
```
