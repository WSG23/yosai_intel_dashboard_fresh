# Error Handling Overview

The `core.error_handling` module provides a flexible framework for capturing
and summarising exceptions across the platform.  It replaces ad-hoc
`try/except` blocks and the minimal JSON handlers defined in
`core.error_handlers`.  All services should migrate to this module for
consistent metrics and logging.

## Usage Patterns

### Registering the middleware

Flask applications can expose unified JSON errors by calling
`register_error_handlers` during initialisation:

```python
from flask import Flask
from yosai_intel_dashboard.src.core.error_handlers import register_error_handlers

app = Flask(__name__)
register_error_handlers(app)
```

This middleware converts custom `YosaiBaseException` instances and generic
`HTTPException` objects into the standard error response format.  Unknown
exceptions are logged and returned as a 500 response.

### Decorator for functions

Use `with_error_handling` to wrap synchronous code.  The decorator automatically
logs the exception, stores it in the global `ErrorHandler` history and returns
`None` (or re-raises if `reraise=True`):

```python
from yosai_intel_dashboard.src.core.error_handling import (
    ErrorCategory,
    ErrorSeverity,
    with_error_handling,
)

@with_error_handling(category=ErrorCategory.DATABASE, severity=ErrorSeverity.HIGH)
def load_records(db):
    return db.query('SELECT * FROM records')
```

Async functions can use `with_async_error_handling` in the same way.

### Circuit breaker and retries

External API calls should use the `CircuitBreaker` utility combined with
`with_retry` to avoid repeated failures:

```python
from yosai_intel_dashboard.src.core.error_handling import CircuitBreaker, with_retry

breaker = CircuitBreaker(name='external_api')

@with_retry(max_attempts=5, delay=2.0)
def fetch_data(client):
    return breaker.call(client.get_data)
```

Metrics for breaker state transitions are exported via Prometheus.

## Migration Guide

1. Import `register_error_handlers` in your app factory and remove any old
   `@app.errorhandler` declarations.
2. Replace manual `try/except` blocks with `with_error_handling` or
   `with_async_error_handling`.  The decorator automatically records context and
   severity.
3. Wrap fragile external service calls with `CircuitBreaker.call` and optionally
   decorate them with `with_retry` for transient failures.
4. Review the recorded history using `error_handler.get_error_summary()` to gain
   insight into error trends.

Moving to this module centralises logging and ensures that Prometheus metrics are
available for all critical exceptions.

## RetryStrategy Guidance

Transient failures often benefit from yosai_intel_dashboard.src.infrastructure.configurable retries. The `RetryStrategy`
mirrors the fields in `ConnectionRetryManager.RetryConfig` and can be tuned per
scenario:

| Failure scenario      | max_attempts | base_delay (s) | backoff_factor | jitter | max_delay (s) |
|-----------------------|--------------|----------------|----------------|--------|---------------|
| Network hiccup        | 5            | 0.5            | 2.0            | ✓      | 5             |
| Database restart      | 10           | 1.0            | 2.0            | ✓      | 30            |

Excessive backoff values can hide persistent outages and delay recovery. Avoid
setting `max_delay` higher than the service's latency budget and keep
`backoff_factor` modest. For production environments, start with conservative
delays, monitor retry metrics and adjust the strategy as real-world behaviour is
observed.
