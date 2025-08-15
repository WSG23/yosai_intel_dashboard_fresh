# Callback Registration and Metrics

`TrulyUnifiedCallbacks` centralizes Dash and event callback management. This guide
covers registration flows, thread-safety and metrics collection, and shows how
Dash callbacks can trigger events.

## Registration Flow

Create a single `TrulyUnifiedCallbacks` instance during application startup and
share it across modules and plugins. Both Dash and event callbacks register
through this manager so conflicts can be detected and metrics aggregated.

```python
from dash import Input, Output
from yosai_intel_dashboard.src.infrastructure.callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent

callbacks = TrulyUnifiedCallbacks(app)
```

### Dash Callbacks

Use the `callback` decorator to register Dash callbacks with explicit
`callback_id` and `component_name` values. The manager tracks these identifiers
to prevent duplicate outputs.

```python
@callbacks.callback(
    Output("result", "children"),
    Input("submit", "n_clicks"),
    callback_id="submit_query",
    component_name="search",
)
def submit_query(n):
    callbacks.trigger_event(CallbackEvent.QUERY_SUBMITTED, {"count": n})
    return f"Submitted {n} times"
```

### Event Callbacks

Event callbacks run outside the Dash lifecycle and can react to custom events.
Registration accepts optional priority, timeout and retry values.

```python
def on_query(data):
    print("query event", data)

callbacks.register_event(CallbackEvent.QUERY_SUBMITTED, on_query)
```

## Thread-Safety

`TrulyUnifiedCallbacks` uses an internal re‑entrant lock. Registration methods
like `callback`, `register_event` and `register_operation` hold this lock while
mutating internal state. This makes callback registration safe even when plugins
initialize concurrently.

## Metrics

Execution metrics for each event are recorded automatically. Retrieve them with
`get_event_metrics` to inspect counts and timing.

```python
metrics = callbacks.get_event_metrics(CallbackEvent.QUERY_SUBMITTED)
print(metrics["calls"], metrics["exceptions"], metrics["total_time"])
```

Metrics are aggregated per event and reset only when the application restarts or
`clear_all_callbacks` is invoked.

## Combined Example

The snippet below shows a Dash callback dispatching an event and a separate
listener reacting to it.

```python
from dash import Input, Output
from yosai_intel_dashboard.src.infrastructure.callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent

callbacks = TrulyUnifiedCallbacks(app)

@callbacks.callback(
    Output("log", "children"),
    Input("btn", "n_clicks"),
    callback_id="process_btn",
    component_name="demo",
)
def process(n):
    callbacks.trigger_event(CallbackEvent.PROCESSED, {"clicks": n})
    return f"Processed {n} clicks"

def on_processed(data):
    print("processed", data)

callbacks.register_event(CallbackEvent.PROCESSED, on_processed)
```

## Asynchronous Event Handlers

Callbacks that perform I/O should be declared with ``async def`` to avoid
blocking the event loop.  Multiple I/O bound tasks can run concurrently with
``asyncio.gather``:

```python
import asyncio

async def store_and_notify(data):
    write = asyncio.to_thread(write_to_disk, data)
    notify = callbacks.trigger_event_async(CallbackEvent.STORED, data)
    await asyncio.gather(write, notify)

callbacks.register_event(CallbackEvent.SAVE_REQUEST, store_and_notify)
```

The ``trigger_event_async`` API ensures event callbacks run concurrently when
possible, making it easier to build responsive handlers.

## Helper Utilities

Common error handling patterns for callbacks are provided by
`safe_execute` and `safe_execute_async` in
`yosai_intel_dashboard.src.infrastructure.callbacks.helpers`. These helpers run a
callable and route exceptions through the central error handler, allowing
callbacks to remain concise:

```python
from yosai_intel_dashboard.src.infrastructure.callbacks.helpers import safe_execute

def risky_operation(x):
    return 10 / x

result, ok = safe_execute(risky_operation, 0, context={"operation": "risky"})
if not ok:
    result = "fallback"
```

Use `safe_execute_async` for asynchronous functions:

```python
from yosai_intel_dashboard.src.infrastructure.callbacks.helpers import safe_execute_async

async def fetch_data():
    ...

data, _ = await safe_execute_async(fetch_data, context={"operation": "fetch"})
```

Both helpers return a tuple of the result and a success flag, making it easy to
share error wrapping across modules.
