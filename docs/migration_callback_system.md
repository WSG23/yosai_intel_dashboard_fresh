# Callback System Migration

This release finalizes the move to the unified callback framework. The
`UnifiedCallbackCoordinator` and its `UnifiedCallbackCoordinatorWrapper` helper
have been removed. Modules should now rely solely on `TrulyUnifiedCallbacks`
for unified callbacks and grouped operations, using `CallbackManager` for event
hooks.

## Migrating

1. Replace any imports of `UnifiedCallbackCoordinator` or the wrapper with
   `TrulyUnifiedCallbacks`.
2. Import `CallbackManager` and `CallbackEvent` from `core` and register event
   hooks using `CallbackManager.register_callback`.
3. Trigger events via `CallbackManager.trigger` or `trigger_async`.
4. Organize multi-step operations using `TrulyUnifiedCallbacks` and call
   `execute_group` within Dash callbacks.

All modules must migrate to this API before upgrading. The legacy wrappers are
no longer shipped with the project.
