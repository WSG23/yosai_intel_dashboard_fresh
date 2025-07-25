from __future__ import annotations

import functools
import logging
from functools import wraps
from typing import Any, Callable, Optional

from yosai_intel_dashboard.src.core.unicode import sanitize_for_utf8

logger = logging.getLogger(__name__)


def unicode_safe_callback(func: Callable[..., Any]) -> Callable[..., Any]:
    """Make callbacks Unicode-safe by sanitizing string inputs."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        safe_args = [sanitize_for_utf8(a) if isinstance(a, str) else a for a in args]
        safe_kwargs = {
            k: sanitize_for_utf8(v) if isinstance(v, str) else v
            for k, v in kwargs.items()
        }
        return func(*safe_args, **safe_kwargs)

    return wrapper


def handle_unicode_surrogates(text: str, processor: Optional[Any] = None) -> str:
    """Handle Unicode surrogate characters safely."""
    if not isinstance(text, str):
        return text
    try:
        if processor and hasattr(processor, "safe_encode_text"):
            return processor.safe_encode_text(text)
        return text.encode("utf-8", errors="ignore").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text.encode("ascii", errors="ignore").decode("ascii")


def handle_safe(*args: Any, **kwargs: Any) -> Callable[[Callable], Callable]:
    """Unified safe callback decorator supporting multiple patterns."""

    # ------------------------------------------------------------------
    def _plugin_decorator(
        app_or_container: Any | None, up: Optional[Any] = None
    ) -> Callable[[Callable], Callable]:
        """Return decorator for plugin style usage."""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*f_args: Any, **f_kwargs: Any):
                callback_service = None
                unicode_proc = up
                container = None
                if hasattr(app_or_container, "_yosai_container"):
                    container = app_or_container._yosai_container
                elif app_or_container and hasattr(app_or_container, "get"):
                    container = app_or_container
                if container:
                    try:
                        callback_service = container.get("json_callback_service")
                    except Exception:
                        try:
                            callback_service = container.get("callback_service")
                        except Exception:
                            callback_service = None
                    if unicode_proc is None:
                        try:
                            unicode_proc = container.get("unicode_processor")
                        except Exception:
                            unicode_proc = None
                safe_func = (
                    callback_service.wrap_callback(func) if callback_service else func
                )
                safe_args = [
                    (
                        handle_unicode_surrogates(a, unicode_proc)
                        if isinstance(a, str)
                        else a
                    )
                    for a in f_args
                ]
                safe_kwargs = {
                    k: (
                        handle_unicode_surrogates(v, unicode_proc)
                        if isinstance(v, str)
                        else v
                    )
                    for k, v in f_kwargs.items()
                }
                result = safe_func(*safe_args, **safe_kwargs)
                if isinstance(result, str):
                    result = handle_unicode_surrogates(result, unicode_proc)
                elif isinstance(result, (list, tuple)):
                    result = [
                        (
                            handle_unicode_surrogates(r, unicode_proc)
                            if isinstance(r, str)
                            else r
                        )
                        for r in result
                    ]
                return result

            return wrapper

        return decorator

    # Detect legacy plugin usage pattern
    if len(args) <= 1 and "callback_id" not in kwargs and "outputs" not in kwargs:
        app_or_container = args[0] if args else None
        if callable(app_or_container) and not hasattr(app_or_container, "callback_map"):
            func = app_or_container
            return _plugin_decorator(None)(func)
        return _plugin_decorator(app_or_container, kwargs.get("unicode_processor"))

    # ------------------------------------------------------------------
    # Legacy registration style: handle_safe(outputs, inputs, callback_id=..., manager=...)
    outputs = args[0] if args else kwargs.pop("outputs")
    inputs = args[1] if len(args) > 1 else kwargs.pop("inputs", None)
    manager = kwargs.pop("manager", None)
    callback_id = kwargs.pop("callback_id", "unknown")
    component_name = kwargs.pop("component_name", "app_factory")
    unicode_proc = kwargs.pop("unicode_processor", None)

    if manager is None:
        raise TypeError("manager required for registration style usage")

    plugin_deco = _plugin_decorator(getattr(manager, "app", None), unicode_proc)

    def decorator(func: Callable) -> Callable:
        wrapped = plugin_deco(func)

        def error_wrapper(*f_args: Any, **f_kwargs: Any):
            try:
                return wrapped(*f_args, **f_kwargs)
            except Exception as exc:  # pragma: no cover - log and continue
                logger.error(f"Callback {callback_id} failed: {exc}")
                if isinstance(outputs, (list, tuple)):
                    return ["Error"] * len(outputs)
                return "Error"

        return manager.unified_callback(
            outputs,
            inputs,
            callback_id=callback_id,
            component_name=component_name,
            **kwargs,
        )(error_wrapper)

    return decorator


safe_callback = handle_safe


def handle_unified(
    target: Any, *cb_args: Any, **cb_kwargs: Any
) -> Callable[[Callable], Callable]:
    """Return decorator registering callbacks on any supported target."""
    from .callback_unifier import CallbackUnifier

    return CallbackUnifier(target, safe_callback(target))(*cb_args, **cb_kwargs)


__all__ = ["unicode_safe_callback", "handle_safe", "handle_unified", "safe_callback"]
