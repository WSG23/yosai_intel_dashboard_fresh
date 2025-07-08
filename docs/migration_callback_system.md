# Callback System Migration

This release introduces a new `TrulyUnifiedCallbacks` class that consolidates the former `CallbackManager` and `UnifiedCallbackCoordinator` concepts. It exposes event registration, Dash callback handling and operation groups in one thread-safe API.

## Migrating

1. Import `CallbackManager` and `CallbackEvent` from `core`.
2. Register hooks using `CallbackManager.register_callback` with the appropriate `CallbackEvent`.
3. Trigger callbacks via `CallbackManager.trigger` or `trigger_async`.
4. Instantiate `TrulyUnifiedCallbacks(app)` and use `register_event` and `register_callback` directly without the wrapper layer.

During migration both systems could coexist, but the recommended approach is to migrate to `TrulyUnifiedCallbacks` for all new development.
