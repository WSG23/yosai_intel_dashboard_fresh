# Async Analytics Service Migration

This guide explains how to migrate from the synchronous analytics service to the new asynchronous
implementation. The async version relies on FastAPI coroutines and non-blocking database access to
improve throughput.

## Key Differences from the Synchronous Service

- **Non-blocking database access** – uses an async SQLAlchemy engine instead of the traditional
  thread-based connections.
- **Awaitable service methods** – endpoints return coroutines and no longer offload work to a thread
  executor.
- **Redis caching** – leverages `redis.asyncio` to share cached results across workers.

The synchronous service can still be used for compatibility, but new deployments should prefer the
async service for better scalability.

## Setting up the Async Engine

1. Install the async dependencies:
   ```bash
   pip install sqlalchemy[asyncio] asyncpg redis
   ```
2. Create the engine and session factory on startup:
   ```python
   from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

   engine = create_async_engine(db_url, pool_size=5)
   Session = async_sessionmaker(engine, expire_on_commit=False)
   ```
3. Inject `Session` into your routes or services and `await` database operations.

## Redis Cache Configuration

Use the built-in `redis.asyncio` client to share cache entries:

```python
import redis.asyncio as redis

redis_cache = redis.Redis(host="localhost", port=6379, decode_responses=True)
```

Pass this client to your services (e.g., `RBACService`) so results are cached across all
processes.

## Benchmarking Performance

Run the performance tests to compare the async and sync implementations:

```bash
pytest -k performance
```

The benchmarks measure request latency and memory usage under load. Refer to the test output for
details on any regressions.
