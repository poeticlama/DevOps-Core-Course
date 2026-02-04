# DevOps Info Service (Python)

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

## Docker

### Build image

```bash
docker build -t <image_name>:<tag> .
```

### Run container

```bash
docker run -p 8080:8080 <image_name>:<tag>
```

### Pull from Docker Hub

```bash
docker pull poeticlama/devops-info-service:1.0
```
