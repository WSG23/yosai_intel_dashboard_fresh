from __future__ import annotations

"""Base component and mixins providing simple dependency injection."""

from typing import Any, Mapping
import logging
import types
import warnings
from functools import wraps


class BaseComponent:
    """Store provided dependencies as immutable attributes."""

    def __init__(self, **dependencies: Any) -> None:  # noqa: D401 - simple container
        for name, value in dependencies.items():
            object.__setattr__(self, name, value)
        object.__setattr__(
            self, "_dependencies", types.MappingProxyType(dict(dependencies))
        )

    def __setattr__(self, key: str, value: Any) -> None:  # pragma: no cover - simple
        if key in getattr(self, "_dependencies", {}):
            raise AttributeError(f"Dependency '{key}' is immutable")
        object.__setattr__(self, key, value)


def handle_deprecated(*param_names: str):
    """Allow positional args for backwards compat with a warning."""

    def decorator(init):
        @wraps(init)
        def wrapped(self, *args, **kwargs):
            if args:
                warnings.warn(
                    f"Positional arguments for {self.__class__.__name__} are deprecated; "
                    "use keyword arguments instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                for arg, name in zip(args, param_names):
                    kwargs.setdefault(name, arg)
            return init(self, **kwargs)

        return wrapped

    return decorator


class LoggingMixin:
    """Provide a simple logging helper."""

    logger: logging.Logger | None = None

    def log(self, level: int, msg: str, *args, **kwargs) -> None:
        logger = self.logger or logging.getLogger(self.__class__.__name__)
        logger.log(level, msg, *args, **kwargs)


class EventDispatchMixin:
    """Mixin requiring an ``event_bus`` dependency for dispatching."""

    event_bus: Any

    def dispatch_event(self, event_type: str, data: Mapping[str, Any]) -> None:
        if not hasattr(self, "event_bus"):
            raise AttributeError("event_bus dependency required")
        self.event_bus.publish(event_type, data)
