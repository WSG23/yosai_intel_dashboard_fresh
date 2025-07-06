# State Management

State is stored in several `dcc.Store` components placed in the base layout.
These stores keep the client in sync across pages without relying on global
variables.

- **global-store** – application wide state shared by all users.
- **session-store** – data scoped to the current user session.
- **app-state-store** – cross page flags such as the initial load marker.
- **theme-store** – remembers the selected color theme.

Callbacks read and write to these stores via the `data` property. Example:

```python
@app.callback(Output('session-store', 'data'), Input('logout-btn', 'n_clicks'))
def clear_session(_):
    return {}
```

Use these stores instead of hidden inputs to avoid race conditions during
multiple callback updates.
