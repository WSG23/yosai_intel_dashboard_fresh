# Developer Onboarding

Get a local environment running quickly.

## Tools

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Make

## Setup

```bash
git clone <repo-url>
cd yosai_intel_dashboard_fresh
python -m venv .venv && source .venv/bin/activate
./scripts/setup.sh && npm install
cp .env.example .env  # set SECRET_KEY and DB_PASSWORD
docker compose -f docker-compose.dev.yml up --build
```

## Environment Variables

- `SECRET_KEY` – required to start the API.
- `DB_PASSWORD` / `DATABASE_URL` – database credentials.
- `TRACING_EXPORTER` – select `jaeger` or `zipkin` for tracing (optional).

## Make Targets

- `make test-quick` – run unit tests.
- `make test-cov` – run tests with coverage.
- `make lint` – execute linters.
- `make format` – apply formatting.

## Common Pitfalls

- Missing `SECRET_KEY` causes the server to exit on startup.
- Skipping `npm install` breaks the CSS build.
- Docker not running results in services being unreachable.
- Forgetting to activate the virtual environment leads to missing packages.

