# Callback Architecture

The dashboard routes events through a unified callback layer. `TrulyUnifiedCallbacks`
wraps the Dash app and exposes a single `.callback` decorator. This decorator
behaves like `app.callback` but also registers the function with the internal
`CallbackManager`.

## Registering Callbacks

```python
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from core.callback_events import CallbackEvent

callbacks = TrulyUnifiedCallbacks(app)

@callbacks.callback(Output('output', 'children'), Input('btn', 'n_clicks'))
def handle_click(n):
    return f"Clicked {n} times"
```

Plugins can register their own hooks by implementing `register_callbacks(manager, container)`.
The manager dispatches events defined in `CallbackEvent` so separate modules can
react to analytics completion, file uploads and security incidents.
