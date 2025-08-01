# Service Container

The dashboard uses a lightweight dependency injection container to wire together services.
`ServiceContainer` from `core.service_container` manages service lifetimes and resolves
implementations by name or protocol. Components fall back to the container when an
explicit instance is not supplied.

## Registering Services

Create a container and register implementations with the desired lifetime:

```python
from yosai_intel_dashboard.src.simple_di import ServiceContainer
from yosai_intel_dashboard.src.services.analytics_service import AnalyticsService
from yosai_intel_dashboard.src.services.interfaces import AnalyticsServiceProtocol
from validation import FileValidator

container = ServiceContainer()
container.register_singleton(
    "analytics",
    AnalyticsService,
    protocol=AnalyticsServiceProtocol,
)
container.register_transient("validator", FileValidator)
container.register_scoped("request_logger", RequestLogger)
```

`register_singleton` stores one instance for the entire application. Use
`register_transient` for a new instance each time `get()` is called. Scoped
registrations create a single instance per logical scope.

## Service Lifetimes

The `ServiceLifetime` enumeration defines how instances are cached:

- **SINGLETON** – one shared instance for the lifetime of the container.
- **TRANSIENT** – a new instance is created on every resolution.
- **SCOPED** – a unique instance is created per scope.

A factory callable can also be supplied to lazily construct an implementation
only when it is first requested.

## Example Usage

Retrieve services by key anywhere in the application:

```python
analytics = container.get("analytics")
validator = container.get("validator")
```

Attach the container to the app during startup so callbacks and plugins can
resolve dependencies on demand.
