"""Common utilities for dependency injection components."""
from .base import BaseComponent, LoggingMixin, EventDispatchMixin, handle_deprecated

__all__ = ["BaseComponent", "LoggingMixin", "EventDispatchMixin", "handle_deprecated"]
