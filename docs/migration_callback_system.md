# Callback System Migration

This release introduces a new `CallbackManager` and `CallbackEvent` API used across the application. Existing modules may still rely on `UnifiedCallbackCoordinator` for Dash callbacks. The helper class `UnifiedCallbackCoordinatorWrapper` bridges both systems and allows registering event callbacks while keeping the old interface intact. With the latest update, these have been replaced by `TrulyUnifiedCallbacks` which exposes a single unified interface.

## Migrating

1. Import `CallbackManager` and `CallbackEvent` from `core`.
2. Register hooks using `CallbackManager.register_callback` with the appropriate `CallbackEvent`.
3. Trigger callbacks via `CallbackManager.trigger` or `trigger_async`.
4. For modules expecting `UnifiedCallbackCoordinator`, use `TrulyUnifiedCallbacks` instead.

During migration, both systems can coexist. Once all modules use the new API directly, the wrapper can be removed.
