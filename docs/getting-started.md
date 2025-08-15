# Getting Started

This guide shows how to run the Yōsai Intel Dashboard either with Docker or on your local machine.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Make
- Docker and Docker Compose

## Clone and Install

```bash
git clone <repo-url>
cd yosai_intel_dashboard_fresh
python -m venv .venv && source .venv/bin/activate
./scripts/setup.sh && npm install
```

## Configure Environment

```bash
cp .env.example .env
# Update SECRET_KEY and DB_PASSWORD as needed
```

## Run with Docker

```bash
docker compose up --build
```

## Run Locally

If you prefer to run the app without Docker:

1. Ensure Postgres and other dependencies are running. The easiest way is to start them via Docker Compose:
   ```bash
   docker compose up db
   ```
2. Start the API in one terminal:
   ```bash
   uvicorn wsgi:app --reload --port 5001
   ```
3. Start the web client in another terminal:
   ```bash
   npm start
   ```

## Verify Setup

Run basic checks to confirm everything works:

```bash
make lint
make test-quick
```

## Troubleshooting

### Port already in use
Another service may be using the required port. Stop the conflicting process or adjust the port in `.env`.

### `SECRET_KEY` missing
The API refuses to start without a `SECRET_KEY`. Ensure your `.env` file defines it before running.

### Docker daemon not running
`docker compose` commands will fail if Docker isn't running. Start the Docker service and retry.
