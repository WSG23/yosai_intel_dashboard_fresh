# State Management

Legacy pages used several `dcc.Store` components placed in the base layout to
share data between callbacks. The new React frontend relies on a global Zustand
store located under `src/state` instead of Dash stores.

- **global-store** – application wide state shared by all users.
- **session-store** – data scoped to the current user session.
- **app-state-store** – cross page flags such as the initial load marker.
- **theme-store** – remembers the selected color theme.

Callbacks previously read and wrote to these stores via the `data` property.
Example:

```python
@app.callback(Output('session-store', 'data'), Input('logout-btn', 'n_clicks'))
def clear_session(_):
    return {}
```

Use these stores instead of hidden inputs to avoid race conditions during
multiple callback updates.
