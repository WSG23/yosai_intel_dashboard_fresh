# Callback System Migration

This release finalizes the move to the unified callback framework. The
The legacy coordinator classes have been removed. Modules should now rely solely
on `TrulyUnifiedCallbacks`,
`CallbackManager` for event hooks and, when multiple steps need to be executed,
`UnifiedCallbackManager` (the alias of `TrulyUnifiedCallbacks` exported from
`core.callbacks`).

## Migrating

1. Import `TrulyUnifiedCallbacks` for registering Dash callbacks.
2. Import `CallbackManager` and `CallbackEvent` from `core` and register event
   hooks using `CallbackManager.register_callback`.
3. Trigger events via `CallbackManager.trigger` or `trigger_async`.
4. Organize multi-step operations using `UnifiedCallbackManager` imported from
   `core.callbacks` (alias of `TrulyUnifiedCallbacks`) and call `execute_group`
   within Dash callbacks.


All modules must migrate to this API before upgrading. The legacy wrappers are
no longer shipped with the project.

## Cleanup Utility Example

The repository ships a small helper script that removes any remaining
references to the legacy controller. It can be run from the project root:

```bash
python tools/complete_callback_cleanup.py
```

The script scans for deprecated imports, rewrites them to use
`TrulyUnifiedCallbacks`, validates that `services/data_processing/callback_controller.py`
is absent and performs a simple runtime check of the new system.
