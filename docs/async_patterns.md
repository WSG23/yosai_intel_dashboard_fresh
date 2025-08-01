# Async Patterns

Guidelines for writing asynchronous code across the dashboard.

## When to use async functions

- Use async for IO bound operations such as database calls or HTTP requests.
- Avoid async for heavy CPU bound work; move those tasks to worker threads or processes.
- Prefer async only when the caller can take advantage of concurrency.

## Utilities in `core.async_utils`

Several helpers simplify coroutine execution:

```python
from yosai_intel_dashboard.src.core.async_utils import gather_n, run_sync

# Run a blocking function in a thread
result = await run_sync(blocking_func, *args)

# Collect results from many coroutines with a concurrency limit
results = await gather_n(tasks, limit=5)
```

Refer to the module docstrings for full details.

## Error handling

Decorate coroutines with `with_async_error_handling` to ensure exceptions are logged:

```python
from yosai_intel_dashboard.src.core.error_handling import with_async_error_handling

@with_async_error_handling()
async def fetch_data(client):
    return await client.get()
```

This captures stack traces and routes them through the standard error handler.

## Testing tips

Use the `async_runner` fixture to execute async code within pytest:

```python
def test_fetch(async_runner):
    result = async_runner(fetch_data(client))
    assert result.status == 200
```

This fixture runs the coroutine on a dedicated event loop, keeping tests fast and isolated.
