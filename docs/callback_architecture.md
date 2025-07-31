# Callback Architecture

The dashboard routes events through a unified callback layer. `TrulyUnifiedCallbacks`
wraps the Dash app and exposes a single `.callback` (alias `.unified_callback`)
decorator. This behaves like `app.callback` but also registers the function with
the internal callback registry so callbacks can be tracked and grouped by
namespace.

## Registering Callbacks

```python
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from core.callback_events import CallbackEvent

callbacks = TrulyUnifiedCallbacks(app)

``callbacks`` should be created once during application startup and
shared with all modules and plugins for registration. Avoid instantiating
``TrulyUnifiedCallbacks`` in individual modules.

@callbacks.callback(Output('output', 'children'), Input('btn', 'n_clicks'))
def handle_click(n):
    return f"Clicked {n} times"
```

Plugins can register their own hooks by implementing `register_callbacks(manager, container)`.
The manager dispatches events defined in `CallbackEvent` so separate modules can
react to analytics completion, file uploads and security incidents.

## Namespaced Callbacks

Each Dash callback should specify a unique `callback_id` and `component_name`.
This allows the system to group callbacks by namespace and detect conflicts.

```python
@callbacks.unified_callback(
    Output("result", "children"),
    Input("submit", "n_clicks"),
    callback_id="submit_query",
    component_name="search",
)
def submit_query(n):
    return f"Submitted {n} times"
```

## Handling Events

`CallbackManager` delivers application events outside of Dash callbacks.

```python
from core.callbacks import TrulyUnifiedCallbacks as CallbackManager
from core.callback_events import CallbackEvent

events = CallbackManager()

def on_complete(info: dict) -> None:
    print("Analysis done", info)

events.register_callback(CallbackEvent.ANALYSIS_COMPLETE, on_complete)
```

## Grouped Operations

`TrulyUnifiedCallbacks` can execute a series of operations sequentially. This is useful when a Dash callback needs to orchestrate multiple steps.


```python
from core.callbacks import TrulyUnifiedCallbacks

ops = TrulyUnifiedCallbacks()
ops.register_operation("refresh", load_data)
ops.register_operation("refresh", update_summary)

@callbacks.unified_callback(Output("out", "children"), Input("btn", "n_clicks"))
def refresh(btn):
    results = ops.execute_group("refresh", btn)
    return str(results[-1])
```

For IO heavy steps you can execute the group concurrently:

```python
results = await ops.execute_group_async("refresh", btn)
```

## Consolidated Callback Management

A single startup task should orchestrate all callback registration steps to prevent duplicated logic:

1. Auto-discover component managers and plugins.
2. Register Dash and event callbacks through one `TrulyUnifiedCallbacks` instance.
3. Deduplicate IDs using `GlobalCallbackRegistry` and expose conflict details.
4. Provide a unified decorator so modules never call `app.callback` directly.
5. Import `TrulyUnifiedCallbacks` from `core.truly_unified_callbacks` in new
   code. Avoid deprecated aliases like `MasterCallbackSystem`.

Running this task at initialization ensures consistent behavior and avoids code conflicts across the application.
