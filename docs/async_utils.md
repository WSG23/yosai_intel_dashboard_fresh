# Async Utilities

This package provides a set of helper primitives used when writing asynchronous
code. The utilities live under `core.async_utils`.

## AsyncContextManager

```python
from yosai_intel_dashboard.src.core.async_utils import AsyncContextManager

async def acquire():
    ...

async def release(exc_type, exc, tb):
    ...

async with AsyncContextManager(acquire, release) as resource:
    ...
```

## async_retry

```python
from yosai_intel_dashboard.src.core.async_utils import async_retry

@async_retry(max_attempts=5, base_delay=1)
async def unreliable_call():
    ...
```

`async_retry` can also be used as a helper to run a coroutine with retries.

## CircuitBreaker

```python
from yosai_intel_dashboard.src.core.async_utils import CircuitBreaker

cb = CircuitBreaker(5, 60)

@cb
async def call_service():
    ...
```

The behaviour matches the previous implementation in
`services.resilience.circuit_breaker`.

## async_batch

```python
from yosai_intel_dashboard.src.core.async_utils import async_batch

async for chunk in async_batch(items, size=100):
    ...
```

`async_batch` works with both regular and asynchronous iterables and yields
lists of the specified batch size.
