# Application Architecture

The dashboard is organized around a small core that wires together services and database models through a dependency injection (DI) container. The entry point is an application factory which creates the Dash/Flask app and registers all services.

![Architecture Diagram](architecture.svg)

1. **App Factory** – Initializes the Flask app and configures extensions.
2. **DI Container** – Provides application-wide services and resolves dependencies.
3. **Services** – Encapsulate business logic and rely on models for data access.
4. **Models** – Data representations loaded from or persisted to the database.
5. **Database** – PostgreSQL, SQLite, or a mock backend configured in `config/`.

The factory builds the container, which then instantiates services. Services operate on models retrieved from the database layer. This layered approach keeps components loosely coupled and easy to test.

## Latest Changes

- **Unified Validator** – Input and file validation are now handled by the
  `SecurityValidator` together with `UnifiedFileValidator`. The deprecated
  `SecureFileValidator` class has been removed.
- **Separated Analytics Modules** – The previously monolithic
  `AnalyticsService` has been broken into smaller modules under
`services/data_processing/` and `analytics/`.  `UnifiedFileValidator`,
`Processor` and `AnalyticsEngine` handle file loading, cleaning and metric
generation while controllers manage UI callbacks.

The deprecated `DataLoader` and `DataLoadingService` modules have been
**removed**. Migrate any remaining code to use
`services.data_processing.processor.Processor` instead.

## Service Lookup

Common services like configuration and analytics are obtained from the DI
container. Register them during application startup and retrieve them where
needed:

```python
from config import create_config_manager
from core.container import Container
from services.analytics_service import create_analytics_service

container = Container()
container.register("config", create_config_manager())
container.register("analytics", create_analytics_service())

config_manager = container.get("config")  # ConfigurationProtocol
analytics_service = container.get("analytics")  # AnalyticsServiceProtocol
```

`create_config_manager()` automatically selects the YAML file to load based on
`YOSAI_ENV` or `YOSAI_CONFIG_FILE`. It can also be used directly:


```python
from config import create_config_manager

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
