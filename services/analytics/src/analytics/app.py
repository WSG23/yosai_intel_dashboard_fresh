"""Compatibility wrapper for tests.

This module exposes the FastAPI ``app`` object from the real analytics
microservice implementation located in
``yosai_intel_dashboard.src.services.analytics_microservice``.  It allows
imports to use ``services.analytics.app`` uniformly for both service and
CLI contexts.
"""

from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING, Awaitable, Callable, Mapping, Protocol, cast


class ASGIApp(Protocol):
    async def __call__(
        self,
        scope: Mapping[str, object],
        receive: Callable[[object], Awaitable[object]],
        send: Callable[[object], Awaitable[None]],
    ) -> None:
        ...


if TYPE_CHECKING:
    _mod: ModuleType
else:  # pragma: no cover - runtime import only
    _mod = import_module("yosai_intel_dashboard.src.services.analytics_microservice.app")

app = cast(ASGIApp, getattr(_mod, "app"))

__all__ = ["app"]
