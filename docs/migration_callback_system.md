# Callback System Migration

This release introduces a new `CallbackManager` and `CallbackEvent` API used across the application. Existing modules may still rely on `UnifiedCallbackCoordinator` for Dash callbacks. The helper class `UnifiedCallbackCoordinatorWrapper` bridges both systems and allows registering event callbacks while keeping the old interface intact.

## Migrating

1. Import `CallbackManager` and `CallbackEvent` from `core`.
2. Register hooks using `CallbackManager.register_callback` with the appropriate `CallbackEvent`.
3. Trigger callbacks via `CallbackManager.trigger` or `trigger_async`.
4. For modules expecting `UnifiedCallbackCoordinator`, wrap it with `UnifiedCallbackCoordinatorWrapper` and pass a `CallbackManager` instance.

During migration, both systems can coexist. Once all modules use the new API directly, the wrapper can be removed.
