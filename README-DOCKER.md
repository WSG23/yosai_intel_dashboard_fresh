# Docker Quickstart

This guide covers common Docker workflows for the Yosai Intel Dashboard. All
services are defined in a single `docker-compose.yml` and configured via `.env`
files.

## Building Images

Build all images referenced in the compose file:

```bash
docker compose build
```

Individual images may be built directly, for example the API service:

```bash
docker build -t yosai-api -f Dockerfile .
```

On Apple Silicon hardware use the `--platform` flag to build `linux/amd64`
images compatible with Intel based hosts:

```bash
docker build --platform=linux/amd64 -t yosai-api -f Dockerfile .
```

## Dockerfiles

The repository contains several Dockerfiles:

- `Dockerfile` – builds the analytics backend.
- `Dockerfile.gateway` – builds the gateway service.
- `api/Dockerfile` – builds the API service.
- `dashboard/Dockerfile` – builds the dashboard UI.

## Running Services

Start the full stack using Docker Compose:

```bash
docker compose up -d
```

Run a single service by specifying its name:

```bash
docker compose up -d api
```

## Environment Variables

Most services read configuration from environment variables. You can export
variables in your shell or create a `.env` file that Docker Compose will load
automatically.

Example shell exports:

```bash
export SECRET_KEY=dev
export DATABASE_URL=postgresql://user:pass@db:5432/app
```

### Proxy Configuration

When working behind a corporate proxy set the standard proxy variables before
running Docker commands:

```bash
export HTTP_PROXY=http://proxy.corp.example:3128
export HTTPS_PROXY=http://proxy.corp.example:3128
export NO_PROXY=localhost,127.0.0.1,.internal
```

These variables are respected by Docker and the services inside the containers.

## Viewing Logs

Follow logs for all services:

```bash
docker compose logs -f
```

Or focus on a single service:

```bash
docker compose logs -f api
```

## Health Probes

Services expose a `/health` endpoint that can be used for liveness and readiness checks.

### Docker Compose

Add a healthcheck to `docker-compose.yml`:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 5
```

### Kubernetes

Configure probes in your pod spec:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

## Troubleshooting

### Missing Dependencies

If a container fails to start due to a missing system dependency (for example
`apache-flink`), install it on the host and rebuild the image:

```bash
sudo apt-get update && sudo apt-get install apache-flink
# then
docker compose build --no-cache <service>
```

### Optional cryptography warning

Some features emit a warning when `cryptography.fernet` is absent. Install the
extra package to silence the message and enable encrypted tokens:

```bash
pip install cryptography
```

### Architecture Mismatch

Images built on Apple Silicon may not run on Intel machines. Always specify
`--platform=linux/amd64` when building on ARM hardware to ensure compatibility.

## Running Tests

Verify the health endpoint with pytest:

```bash
pytest tests/test_health_endpoint.py
```
