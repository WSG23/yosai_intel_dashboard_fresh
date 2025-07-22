# API Documentation

The Flask routes expose a minimal API used by the dashboard. A Swagger UI is
available at `/api/docs` when the application is running. To regenerate the
OpenAPI specification run:

```bash
go run ./api/openapi
```

The script writes `docs/openapi.json`. Once generated, this file can be served
by Swagger UI to display the complete API reference.

The CI workflow runs this command and uploads the generated `openapi.json` as an
artifact so the specification is available from workflow runs.

### Generating API clients

Use [OpenAPI Generator](https://openapi-generator.tech/) to create typed clients
for the access event service:

```bash
npx openapi-generator-cli generate -i api/contracts/access-event.yaml -g go -o pkg/eventclient
npx openapi-generator-cli generate -i api/contracts/access-event.yaml -g python -o analytics/clients/event_client
```

The commands write the Go client under `pkg/eventclient` and the Python client
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
When backwards-incompatible changes are introduced, a new version path will be
added while the old one is maintained for a period of time. Clients should
specify the exact version in requests to avoid unexpected behavior.

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

## Route Permissions

The following table lists the required role or permission for key API route groups.

| Route Prefix | Required Role | Required Permission |
|--------------|---------------|--------------------|
| `/admin` | `admin` | - |
| `/api/v1/analytics` | - | `analytics.read` |
| `/api/v1/events` | - | `events.write` |
| `/api/v1/doors` | - | `doors.control` |
