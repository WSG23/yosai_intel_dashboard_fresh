"""Base building block for application components (see ADR 0001)."""

from __future__ import annotations


class BaseComponent:
    """Provide a lightweight base implementation for components.

    ``BaseComponent`` now accepts arbitrary keyword arguments which are stored
    on the instance.  This enables lightweight dependency injection without
    having to override ``__init__`` in every subclass.  Subclasses can simply
    call ``super().__init__(service=svc)`` and the ``service`` attribute will be
    available on ``self``.
    """

    def __init__(self, component_id: str | None = None, **dependencies) -> None:
        self.component_id = component_id or self.__class__.__name__
        for name, value in dependencies.items():
            setattr(self, name, value)


__all__ = ["BaseComponent"]
