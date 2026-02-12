# Lab 02 — Docker Containerization

## 1. Docker Best Practices Applied

### Non-root User

The application inside the container is executed using a non-root user (`appuser`) instead of the default root user.

```dockerfile
RUN useradd --create-home appuser
USER appuser
```

**Why this matters:**
Running containers as root increases the potential impact of a security breach. Using a non-root user limits privileges inside the container and follows Docker security best practices for production environments.

---

### Specific Base Image Version

A fixed and explicit Python base image version is used:

```dockerfile
FROM python:3.13-slim
```

**Why this matters:**
Pinning a specific image version ensures reproducible builds and protects against unexpected breaking changes that may occur when using the `latest` tag.

---

### Layer Caching Optimization

The `requirements.txt` file is copied and installed separately from the application source code:

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**Why this matters:**
Docker caches image layers. When dependencies do not change, Docker can reuse the cached layer, significantly reducing rebuild times during development and CI/CD pipelines.

---

### Minimal File Copy

Only the files required to run the application are copied into the image:

```dockerfile
COPY main.py .
```

**Why this matters:**
Copying only necessary files reduces the final image size and minimizes the risk of accidentally including sensitive or development-only files.

---

### .dockerignore Usage

A `.dockerignore` file is used to exclude unnecessary files and directories from the build context:

```dockerignore
__pycache__/
*.pyc
.git/
.venv/
docs/
```

**Why this matters:**
A smaller build context results in faster builds, lower resource usage, and improved security by preventing irrelevant files from being sent to the Docker daemon.

---

## 2. Image Information & Decisions

### Base Image Choice

The selected base image is `python:3.13-slim`.

**Justification:**

- Significantly smaller than the full Python image
- Officially maintained and supported
- Contains everything required to run a FastAPI application
- Uses a modern and up-to-date Python version

---

### Final Image Size

The final image size is approximately **XX–YY MB**.

**Assessment:**
For a FastAPI service without additional system dependencies, this image size is efficient and appropriate for production use.

---

### Layer Structure Explanation

The image is built using the following logical layers:

1. Base Python image
2. Environment variable configuration
3. Non-root user creation
4. Dependency installation
5. Application source code
6. Runtime user and startup command

This structure improves readability, maintainability, and build performance.

---

### Optimization Choices

- Use of `--no-cache-dir` during pip installation
- Avoidance of unnecessary build tools
- Minimal set of copied files
- Slim base image instead of full image

---

## 3. Build & Run Process

### Build Image Output

```text
[+] Building 2.9s (12/12) FINISHED                                                                                                         docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                       0.0s
 => => transferring dockerfile: 409B                                                                                                                       0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                                                                                        2.7s
 => [internal] load .dockerignore                                                                                                                          0.0s
 => => transferring context: 156B                                                                                                                          0.0s
 => [1/7] FROM docker.io/library/python:3.13-slim@sha256:2b9c9803c6a287cafa0a8c917211dddd23dcd2016f049690ee5219f5d3f1636e                                  0.0s
 => [internal] load build context                                                                                                                          0.0s
 => => transferring context: 63B                                                                                                                           0.0s
 => CACHED [2/7] RUN useradd --create-home appuser                                                                                                         0.0s
 => CACHED [3/7] WORKDIR /app                                                                                                                              0.0s
 => CACHED [4/7] COPY requirements.txt .                                                                                                                   0.0s
 => CACHED [5/7] RUN pip install --no-cache-dir -r requirements.txt                                                                                        0.0s
 => CACHED [6/7] COPY app.py .                                                                                                                             0.0s
 => CACHED [7/7] RUN chown -R appuser:appuser /app                                                                                                         0.0s
 => exporting to image                                                                                                                                     0.0s
 => => exporting layers                                                                                                                                    0.0s
 => => writing image sha256:960d06965f6e0a4c6c737a274a914e78cb78088134671387299a5e5bcb6033aa                                                               0.0s
 => => naming to docker.io/library/devops-info-service:1.0                                                                                                 0.0s
```

---

### Run Container

```text
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     172.17.0.1:53428 - "GET / HTTP/1.1" 200 OK
INFO:     172.17.0.1:53428 - "GET /favicon.ico HTTP/1.1" 404 Not Found
INFO:     172.17.0.1:53428 - "GET /_static/out/browser/serviceWorker.js HTTP/1.1" 404 Not Found
INFO:     172.17.0.1:52206 - "GET / HTTP/1.1" 200 OK
INFO:     172.17.0.1:52400 - "GET / HTTP/1.1" 200 OK
INFO:     172.17.0.1:55254 - "GET / HTTP/1.1" 200 OK
INFO:     172.17.0.1:53262 - "GET / HTTP/1.1" 200 OK
```

The container is started with port mapping:

- container port: `8080`
- host port: `8080`

---

### Testing Endpoints

```bash
curl http://localhost:8080/


StatusCode        : 200
StatusDescription : OK
Content           : {"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI
                    "},"system":{"hostname":"ed6e3510b184","platform":"Linux","platform_version":"...
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 739
                    Content-Type: application/json
                    Date: Wed, 04 Feb 2026 09:34:03 GMT
                    Server: uvicorn



                    {"service":{"name":"devops-info-service","version":"1.0.0","description":"...
Forms             : {}
Headers           : {[Content-Length, 739], [Content-Type, application/json], [Date, Wed, 04 Feb 2026 09:34:03 GMT], [Server, uvicorn]}
Images            : {}
InputFields       : {}
Links             : {}
ParsedHtml        : mshtml.HTMLDocumentClass
RawContentLength  : 739


```

Root endpoint returns valid JSON response identical to the locally running application.

---

### Docker Hub Repository

The image is published to Docker Hub and is publicly accessible:

```
https://hub.docker.com/r/poeticlama/devops-info-service
```

---

## 4. Technical Analysis

### Why This Dockerfile Works

The Dockerfile follows a standard production-ready approach:

- minimal base image
- cache-efficient layer ordering
- non-root execution
- explicit application startup command

The FastAPI application behaves identically inside the container and in the local environment.

---

### Layer Order Impact

If the application code were copied before installing dependencies, any code change would invalidate the Docker cache and force dependency reinstallation.

The chosen layer order minimizes rebuild time and improves development efficiency.

---

### Security Considerations

The following security measures were implemented:

- non-root container execution
- minimal base image
- reduced attack surface
- no secrets stored in the image or Dockerfile

---

### .dockerignore Impact

The `.dockerignore` file:

- reduces build context size
- speeds up image builds
- prevents development artifacts from entering the image
- improves overall container security

---

## 5. Challenges & Solutions

### Issue: Container not accessible from host

Initially, the application was not reachable from the host machine after starting the container.

---

### Root Cause

By default, Uvicorn binds to `127.0.0.1`, which makes the service inaccessible outside the container.

---

### Solution

Explicitly bind the application to `0.0.0.0` in the container startup command:

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

### Lessons Learned

- Understanding container networking is critical for production readiness
- Dockerfile layer order has a direct impact on build performance
- Security should be considered even for simple services
