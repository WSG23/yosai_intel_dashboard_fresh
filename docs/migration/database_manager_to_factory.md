# Database Manager to Factory Migration

The legacy `DatabaseManager` has been replaced by the `DatabaseManagerFactory` to simplify configuration and improve extensibility. This guide outlines how to migrate existing code to the new factory based approach.

## Legacy Usage

```python
from yosai_intel_dashboard.src.infrastructure.config.database_manager import DatabaseManager, DatabaseSettings

settings = DatabaseSettings(type="sqlite", name="analytics.db")
db = DatabaseManager(settings)
result = db.execute_query("SELECT 1")
db.close_connection()
```

## New Usage

```python
from yosai_intel_dashboard.src.core.plugins.config.factories import DatabaseManagerFactory
from yosai_intel_dashboard.src.infrastructure.config.schema import DatabaseSettings

settings = DatabaseSettings(type="sqlite", name="analytics.db")
db = DatabaseManagerFactory.create_manager(settings)
result = db.execute_query("SELECT 1")
db.close_connection()
```

## Interface Mapping

| Legacy Interface | Factory API | Notes |
|------------------|-------------|-------|
| `DatabaseManager(settings)` | `DatabaseManagerFactory.create_manager(settings)` | Factory selects appropriate manager implementation based on configuration. |
| `get_connection()` | `get_connection()` | Method name unchanged. |
| `test_connection()` | `test_connection()` | Method name unchanged. |
| `execute_query(query, params=None)` | `execute_query(query, params=None)` | Method name unchanged. |
| `close_connection()` | `close_connection()` | Method name unchanged. |

## Deprecations

- Direct instantiation of `DatabaseManager`.
- `ThreadSafeDatabaseManager`.
- `create_database_manager` helper function.

These components are deprecated as of version **2.4.0** and are scheduled for removal in version **3.0.0**.

See the [Deprecation Timeline](../deprecation_timeline.md) for important dates.
