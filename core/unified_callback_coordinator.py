"""Unified callback coordinator with DI integration."""
from __future__ import annotations

from typing import Callable, Any, Dict, List
import dash
from dash.dependencies import Input, Output, State

from core.service_container import ServiceContainer
from core.unicode_processor import safe_format_text, handle_unicode_surrogates


class CallbackRegistry:
    """Registry for managing callbacks with DI."""

    def __init__(self, container: ServiceContainer):
        self.container = container
        self.callbacks: Dict[str, Callable] = {}
        self.app = None

    def register_callback(
        self,
        outputs: List[Output],
        inputs: List[Input],
        states: List[State] = None,
        callback_id: str = None,
    ):
        """Decorator for registering callbacks with DI and Unicode safety."""

        def decorator(func: Callable):
            callback_id_final = callback_id or func.__name__

            # Wrap function with Unicode safety and DI injection
            def wrapped_callback(*args, **kwargs):
                try:
                    # Inject DI container as first argument
                    result = func(self.container, *args, **kwargs)

                    # Handle Unicode surrogates in results
                    if isinstance(result, (list, tuple)):
                        return [handle_unicode_surrogates(item) for item in result]
                    else:
                        return handle_unicode_surrogates(result)

                except Exception as e:
                    print(f"Callback error in {callback_id_final}: {e}")
                    return dash.no_update

            self.callbacks[callback_id_final] = wrapped_callback

            # Register with Dash app if available
            if self.app:
                self.app.callback(
                    outputs,
                    inputs,
                    states or [],
                )(wrapped_callback)

            return wrapped_callback

        return decorator

    def set_app(self, app: dash.Dash):
        """Set the Dash app and register pending callbacks."""
        self.app = app
        # Register any pending callbacks
        for callback_id, callback_func in self.callbacks.items():
            if not hasattr(callback_func, '_dash_registered'):
                callback_func._dash_registered = True


class UnifiedCallbackCoordinator:
    """Coordinates all callbacks with DI integration."""

    def __init__(self, app: dash.Dash, container: ServiceContainer):
        self.app = app
        self.container = container
        self.registry = CallbackRegistry(container)
        self.registry.set_app(app)

    def register_upload_callbacks(self):
        """Register upload callbacks with DI."""
        from services.upload.callbacks import UploadCallbacks
        upload_callbacks = UploadCallbacks(self.registry)
        upload_callbacks.register_all()

    def register_analytics_callbacks(self):
        """Register analytics callbacks with DI."""
        from services.analytics.callbacks import AnalyticsCallbacks
        analytics_callbacks = AnalyticsCallbacks(self.registry)
        analytics_callbacks.register_all()

    def register_all_callbacks(self):
        """Register all application callbacks."""
        self.register_upload_callbacks()
        self.register_analytics_callbacks()


__all__ = ["CallbackRegistry", "UnifiedCallbackCoordinator"]
