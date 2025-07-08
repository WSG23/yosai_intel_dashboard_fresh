import functools
from typing import Any, Callable, Optional


def handle_safe(app_or_container: Any = None) -> Callable:
    """Plugin-aware decorator that uses the JSON serialization plugin"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get callback service from container (via plugin)
            callback_service = None

            if hasattr(app_or_container, "_yosai_container"):
                container = app_or_container._yosai_container
                try:
                    callback_service = container.get("json_callback_service")
                except Exception:
                    # Fallback to generic callback service
                    try:
                        callback_service = container.get("callback_service")
                    except Exception:
                        pass

            if callback_service:
                # Use the plugin's callback service to wrap the callback
                safe_func = callback_service.wrap_callback(func)
                return safe_func(*args, **kwargs)

            # Fallback - execute without service wrapper
            return func(*args, **kwargs)

        return wrapper

    # Handle both @safe_callback and @safe_callback(app) usage
    if callable(app_or_container) and not hasattr(app_or_container, "callback_map"):
        # Direct usage: @safe_callback when a plain function is passed
        func = app_or_container
        return decorator(func)
    else:
        # Parameterized usage: @safe_callback(app)
        return decorator


safe_callback = handle_safe


def handle_unified(target: Any, *cb_args: Any, **cb_kwargs: Any) -> Callable:
    """Return decorator registering callbacks on any supported target."""
    from .callback_unifier import CallbackUnifier

    return CallbackUnifier(target, safe_callback(target))(*cb_args, **cb_kwargs)
__all__ = ["handle_safe", "handle_unified", "safe_callback"]

