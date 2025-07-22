# API Documentation

The Flask routes expose an API used by the dashboard. A Swagger UI is
available at `/api/docs` when the application is running. The complete
OpenAPI description lives in `api/openapi/yosai-api-v2.yaml` and can be
converted to JSON with:

```bash
go run ./api/openapi
```

This writes `docs/openapi.json`. Once generated, this file can be served
by Swagger UI to display the API reference or used to generate client SDKs.

The CI workflow runs this command and uploads the generated `openapi.json` as an
artifact so the specification is available from workflow runs.

### Generating API clients

Use [OpenAPI Generator](https://openapi-generator.tech/) to create typed clients
for the dashboard API. A helper script automates generation:

```bash
./scripts/generate_clients.sh
```

The script writes the Go client under `pkg/eventclient` and the Python client
under `analytics/clients/event_client`.

### Regenerating after changes

Run the generator whenever API routes or schemas change:

```bash
go run ./api/openapi
```

Commit the updated `docs/openapi.json` so the specification stays in sync with
the codebase.

## API Versioning

All endpoints are prefixed with a version such as `/v1` or `/api/v1`.
The Go `versioning` module provides `VersionManager` middleware that extracts
the version from the request path and attaches metadata to the context. The
manager can mark versions as `active`, `deprecated`, or `sunset` to control
behavior. Deprecated versions return a `Warning` header while sunset versions
return a `410 Gone` response.

## Database Manager

### `DatabaseManager`

Factory class for creating database connections.

#### Methods

- `from_environment() -> DatabaseConfig`: Create config from environment variables
- `create_connection(config) -> DatabaseConnection`: Create database connection
- `test_connection(config) -> bool`: Test database connectivity

## Analytics Service

### `AnalyticsService`

Centralized analytics service for dashboard operations.

#### Methods

- `get_dashboard_summary() -> Dict[str, Any]`: Get dashboard overview
- `get_access_patterns_analysis(days) -> Dict[str, Any]`: Analyze access patterns
- `process_uploaded_file(contents, filename) -> Dict[str, Any]`: Validate and parse an uploaded file using `UnifiedFileValidator.validate_file`

## Models

### `AccessEvent`

Represents a single access control event.

#### Attributes

- `event_id: str`: Unique event identifier
- `timestamp: datetime`: When the event occurred
- `person_id: str`: Person attempting access
- `door_id: str`: Door being accessed
- `access_result: AccessResult`: Success/failure of access

## Service Container

`ServiceContainer` in `core.service_container` offers a more capable
dependency injection mechanism. It resolves services by name and caches
instances created by registered factories.

```python
from core.service_container import ServiceContainer

container = ServiceContainer()
container.register_factory("db", DatabaseManager)

# Later in the code
if container.has("db"):
    db = container.get("db")
```
