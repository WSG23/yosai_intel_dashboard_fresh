> **Note**: Import paths updated for clean architecture. Legacy imports are deprecated.

# Application Architecture

The dashboard is organized around a small core that wires together services and database models through a dependency injection (DI) container. The entry point is an application factory which creates the Dash/Flask app and registers all services.

![Architecture Diagram](architecture.svg)

For a high-level overview of how services and data stores interact, see the [System Diagram](system_diagram.md).

1. **App Factory** – Initializes the Flask app and configures extensions.
2. **DI Container** – Provides application-wide services and resolves dependencies.
3. **Services** – Encapsulate business logic and rely on models for data access.
4. **Models** – Data representations loaded from or persisted to the database.
5. **Database** – PostgreSQL, SQLite, or a mock backend configured in `config/`.

The factory builds the container, which then instantiates services. Services operate on models retrieved from the database layer. This layered approach keeps components loosely coupled and easy to test.

See [React Component Architecture](react_component_architecture.md) for an overview of the front-end structure.

## Folder Structure

The codebase is organized into a few top-level directories:

- `core/` – shared framework utilities and base classes
- `services/` – business logic and integration services
- `repositories/` – database access layers
- `plugins/` – optional extensions discovered at runtime

## Latest Changes

- **Unified Validation Package** – Input and file validation are exported from
  the `validation` package. Import `SecurityValidator` and `FileValidator` from
  there instead of referencing the modules directly. The deprecated
  `UnifiedFileValidator` class has been renamed to `FileValidator`.

- **Separated Analytics Modules** – The previously monolithic
  `AnalyticsService` has been broken into smaller modules under
`services/data_processing/` and `analytics/`. `Processor` and `AnalyticsEngine`
handle file loading, cleaning and metric
generation while controllers manage UI callbacks.
- **Service Builder Pattern** – Microservices now create a
  `ServiceBuilder` instance which attaches logging, metrics and health checks
  before the service starts. `BaseService` still exists for compatibility but
  new services should prefer the builder API.
- **Single Service Registry** – Optional services and service discovery live
  under `core.registry`. The old `services.registry` module is a thin
  compatibility shim and will be removed in a future release.

The deprecated `DataLoader` and `DataLoadingService` modules have been
**removed**. Migrate any remaining code to use
`services.data_processing.processor.Processor` instead.

## Service Lookup

Common services like configuration and analytics are obtained from the DI
container. Register them during application startup and retrieve them where
needed:

```python
from yosai_intel_dashboard.src.infrastructure.config import create_config_manager
from yosai_intel_dashboard.src.simple_di import ServiceContainer
from yosai_intel_dashboard.src.services.analytics_service import create_analytics_service

container = ServiceContainer()
container.register("config", create_config_manager())
container.register("analytics", create_analytics_service())

config_manager = container.get("config")  # ConfigurationProtocol
analytics_service = container.get("analytics")  # AnalyticsServiceProtocol
```

`create_config_manager()` automatically selects the YAML file to load based on
`YOSAI_ENV` or `YOSAI_CONFIG_FILE`. It can also be used directly:


```python
from yosai_intel_dashboard.src.infrastructure.config import create_config_manager

config = create_config_manager()
db_cfg = config.get_database_config()
```

The configuration system is split into small dataclasses such as
`AppConfig`, `DatabaseConfig`, `SecurityConfig` and more. The factory
`create_config_manager()` assembles these pieces and applies environment
overrides before returning a ready-to-use `ConfigManager` instance.

Both services implement protocols so alternative implementations can be swapped
in for tests or future extensions.

Additional interfaces such as `ExportServiceProtocol`, `UploadValidatorProtocol`
and `DoorMappingServiceProtocol` are defined in `services/interfaces.py`. When a
component does not receive a concrete instance it falls back to the global
`ServiceContainer` exposed on the Dash app.

## Service Registry

Optional services and microservice endpoints are centralized in
`core.registry`. Use `register_service` and `get_service` to expose or retrieve
services lazily, and `ServiceDiscovery` for best-effort resolution of external
microservices. The previous `services.registry` module simply re-exports these
objects and should no longer be imported directly.

## Service Builder Pattern

New microservices are constructed using `ServiceBuilder` which configures
logging, metrics and health routes before returning the final service
instance:

```python
from yosai_framework.builder import ServiceBuilder

service = (
    ServiceBuilder("analytics")
    .with_config("config/service.yaml")
    .with_logging()
    .with_metrics("0.0.0.0:9000")
    .with_health()
    .build()
)
service.start()
```

Existing code relying directly on `BaseService` can migrate by creating a
`ServiceBuilder` and invoking the same `.start()` method on the built service.

## Service Container Registration

During initialization the factory builds the service container and registers core
services before any plugins are loaded.

```mermaid
graph TB
    A[App Factory] --> B[Create ServiceContainer]
    B --> C[register('config', ConfigManager)]
    B --> D[register('analytics', AnalyticsService)]
    B --> E[register('plugins', PluginManager)]
    E --> F[Discover Plugins]
    F --> G[register additional services]
```

## Plugin Lifecycle

Plugins follow a simple lifecycle once discovered by the plugin manager.

```mermaid
graph TB
    A[Discover Plugins] --> B[Resolve Dependencies]
    B --> C[load()]
    C --> D[configure()]
    D --> E[start()]
    E --> F[Plugin Running]
    F --> G[periodic health_check()]
    G --> F
```

## REST, Queue, and Callback Flow

The following diagram shows the high-level flow between REST endpoints, the
message queue, and callback handlers. Each service lists its incoming and
outgoing data paths along with its dependencies.

```mermaid
flowchart LR
    Client[[Client]] -->|HTTP request| API[REST API Service]
    API -->|enqueue| MQ[Message Queue]
    API -->|write| DB[(Database)]
    MQ -->|deliver| Worker[Worker Service]
    Worker -->|invoke| CB[Callback Service]
    Worker -->|write| DB
    CB -->|HTTP callback| Client
```

- **REST API Service**
  - Ingress: HTTP requests from clients.
  - Egress: messages to **Message Queue**, writes to **Database**.
  - Dependencies: **Message Queue**, **Database**.
- **Worker Service**
  - Ingress: messages from **Message Queue**.
  - Egress: events to **Callback Service**, writes to **Database**.
  - Dependencies: **Message Queue**, **Callback Service**, **Database**.
- **Callback Service**
  - Ingress: events from **Worker Service**.
  - Egress: HTTP callbacks to clients.
  - Dependencies: **Worker Service**.

> **Maintenance**: Update this diagram and the notes above whenever
> cross-service interactions change.

## Callback Registration Sequence

The callback manager registers Dash callbacks and tracks them in the global
registry so plugins can avoid duplicate IDs.

```mermaid
sequenceDiagram
    participant AF as AppFactory
    participant PM as PluginManager
    participant PL as Plugin
    participant CB as TrulyUnifiedCallbacks
    participant REG as GlobalCallbackRegistry

    AF->>PM: discover_plugins()
    PM->>PL: register_callbacks(CB, container)
    PL->>CB: unified_callback(...)
    CB->>REG: register(callback_id)
    REG-->>CB: confirmation
```

## Threat Intelligence Integration

Security callbacks can subscribe to updates from `ThreatIntelligenceSystem`.
External feeds are gathered asynchronously and correlated with internal
logs.  When suspicious patterns are found the
`AutomatedResponseOrchestrator` queues response actions using the global
`task_queue`.  Callback handlers may listen for these queued actions and
respond accordingly.
