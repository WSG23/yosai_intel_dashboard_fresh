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
  `SecurityValidator` exposed through `ValidationMiddleware`.  It replaces the
  older `InputValidator`, `SecureFileValidator` and
  `DataFrameSecurityValidator` classes.
- **Separated Analytics Modules** – The previously monolithic
  `AnalyticsService` has been broken into smaller modules under
  `services/data_processing/` and `analytics/`.  `FileHandler`, `DataProcessor`
  and `AnalyticsEngine` handle file loading, cleaning and metric generation
  while controllers manage UI callbacks.

Developers still using the legacy `DataLoader` or `DataLoadingService` should
migrate to `services.data_processing.processor.Processor` and update imports
accordingly.
