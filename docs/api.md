# API Documentation

The Flask routes expose a minimal API used by the dashboard. A Swagger UI is
available at `/api/docs` when the application is running. To regenerate the
OpenAPI specification run:

```bash
python tools/generate_openapi.py
```

The script writes `docs/openapi.json`. Once generated, this file can be served
by Swagger UI to display the complete API reference.

### Regenerating after changes

`docs/openapi.json` is not committed to the repository. Whenever you modify any
API routes or schemas, run `python tools/generate_openapi.py` and verify the
file in `docs/` updates. This keeps the interactive documentation in sync with
the code.

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
