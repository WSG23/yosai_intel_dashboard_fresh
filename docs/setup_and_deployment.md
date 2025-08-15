# Setup and Deployment Guide

This guide consolidates local development, Docker, and production deployment instructions for the Yōsai Intel Dashboard.

## Prerequisites
- Python 3.12+
- Node.js and npm
- Docker and Docker Compose
- Optional: Kubernetes cluster and [Helm](https://helm.sh/) for production

## Local Development
1. **Clone and enter the repository**
   ```bash
   git clone https://github.com/WSG23/yosai_intel_dashboard_fresh.git
   cd yosai_intel_dashboard_fresh
   ```
2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv && source venv/bin/activate
   pip install -r requirements-dev.txt
   npm ci
   ```
3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # adjust values such as SECRET_KEY and DATABASE_URL
   ```
4. **Start the stack**
   ```bash
   docker compose up --build
   ```
5. **Seed the database with sample data**
   ```bash
   psql -f deployment/database_setup.sql
   ```
6. **Run tests**
   ```bash
   make test-quick    # unit tests
   make test-cov      # coverage report
   ```

## Production Deployment
1. **Build container images**
   ```bash
   docker compose build
   # or build a single image
   docker build -t yosai-api -f Dockerfile .
   ```
2. **Provide required environment variables**
   ```bash
   export SECRET_KEY=<strong-secret>
   export DATABASE_URL=postgresql://user:pass@db:5432/app
   ```
3. **Deploy with Docker Compose**
   ```bash
   docker compose up -d
   ```
4. **Deploy to Kubernetes with ArgoCD and Helm**
   ```bash
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   helm repo add yosai https://example.com/charts && helm repo update
   argocd app create yosai-dashboard \
     --repo https://github.com/WSG23/yosai_intel_dashboard_fresh.git \
     --path helm/chart \
     --dest-server https://kubernetes.default.svc \
     --dest-namespace default
   argocd app sync yosai-dashboard
   ```

## Common Tasks
- **View logs**
  ```bash
  docker compose logs -f            # all services
  docker compose logs -f api       # single service
  ```
- **Run a specific test**
  ```bash
  pytest tests/test_health_endpoint.py
  ```
- **Rebuild CSS bundle**
  ```bash
  npm run build-css
  ```

## Troubleshooting
- Missing system dependency: install the package and rebuild the image.
  ```bash
  sudo apt-get update && sudo apt-get install <package>
  docker compose build --no-cache <service>
  ```
- Optional cryptography warning: install the extra package.
  ```bash
  pip install cryptography
  ```
- Architecture mismatch between ARM and x86 hosts:
  ```bash
  docker build --platform=linux/amd64 -t yosai-api -f Dockerfile .
  ```
- See [docs/troubleshooting.md](troubleshooting.md) for more guidance.
