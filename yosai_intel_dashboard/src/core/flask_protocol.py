from __future__ import annotations

"""Minimal protocol for Flask-like apps."""

from typing import Any, Callable, Iterable, Protocol, runtime_checkable


@runtime_checkable
class FlaskProtocol(Protocol):
    """Simplified interface for objects that behave like :class:`flask.Flask`."""

    config: dict

    def route(
        self, rule: str, methods: Iterable[str] | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...
