# API Documentation

The Flask routes expose a minimal API used by the dashboard. A Swagger UI is
available at `/api/docs` when the application is running. To regenerate the
OpenAPI specification run:

```bash
python tools/generate_openapi.py
```

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
- `process_uploaded_file(df, filename) -> Dict[str, Any]`: Process uploaded data

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

`Container` provides a simple registry for services that can be resolved by
name. It is typically configured during application startup.

```python
from core.container import Container

container = Container()
container.register("db", DatabaseManager())

# Later in the code
if container.has("db"):
    db = container.get("db")
```
