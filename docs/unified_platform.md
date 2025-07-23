# Unified Platform

This release introduces a unified service framework shared between Python and Go implementations. The framework provides common configuration loading, logging, metrics, tracing and graceful shutdown handling.

## Operations

The unified platform bundles all services together using `docker-compose.unified.yml`. The following `make` targets wrap common operations and call the `ops_cli` helper under the hood.

## Available Commands

- `make build-all` – Build Docker images for every service.
- `make test-all` – Run the full test suite.
- `make deploy-all` – Start the entire stack in the background.
- `make logs service=<name>` – Tail logs for a specific service.

The same functionality can be invoked directly via the CLI:

```bash
python -m tools.ops_cli build-all
python -m tools.ops_cli test-all
python -m tools.ops_cli deploy-all
python -m tools.ops_cli logs gateway
```

The repository also includes a small Go wrapper named `yosai` which
forwards commands to `tools.ops_cli` for a chosen service:

```bash
yosai build gateway
yosai test gateway
yosai deploy gateway
yosai logs gateway
```
