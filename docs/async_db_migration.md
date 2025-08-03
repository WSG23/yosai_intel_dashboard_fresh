# Async Database Migration Guide

This release replaces the synchronous `psycopg2` connections with
an asynchronous implementation built on `asyncpg`.
Existing services now rely on an async connection pool which is
created on application startup.

## Key Changes

- New module `services/common/async_db.py` provides pool creation,
  teardown and a simple health check.
- `services/analytics_microservice/async_queries.py` contains the
  SQL helpers used by the FastAPI services.
- Microservice endpoints call these async functions directly rather
  than executing blocking code in a thread executor.
- `core/plugins/config/async_database_manager.py` offers an async
  replacement for the old PostgreSQL manager.
- Configuration adds async pool sizes and timeout values which
  default to the same numbers as the synchronous settings.

## Migrating from `psycopg2`

1. Remove any direct `psycopg2` usage.
2. Import `create_pool` from `services.common.async_db` and create the
   pool during startup using your database connection string.
3. Use the functions in `async_queries.py` (or your own async SQL
   helpers) with the acquired pool.
4. Ensure that any cleanup code calls `close_pool()` on shutdown.
5. Batches default to `MIGRATION_CHUNK_SIZE` rows as defined in
   `config/constants.py`.

The async pool ensures non‑blocking database access and allows the
web server to handle more concurrent requests.

## Best Practices

- Acquire connections using `async with pool.acquire() as conn:` so that
  connections are released back to the pool even if an error is raised.
- Keep connection usage scoped to the smallest possible block and avoid
  storing connections on long‑lived objects.
- Always call `close_pool()` during application shutdown to cleanly
  dispose of the pool and its resources.
