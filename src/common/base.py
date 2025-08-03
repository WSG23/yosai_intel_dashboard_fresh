"""Base building block for application components."""
from __future__ import annotations


class BaseComponent:
    """Provide a lightweight base implementation for components."""

    def __init__(self, component_id: str | None = None) -> None:
        self.component_id = component_id or self.__class__.__name__


__all__ = ["BaseComponent"]

