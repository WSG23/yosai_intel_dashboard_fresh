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
