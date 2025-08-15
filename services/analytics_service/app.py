"""Compatibility wrapper for tests.

The test-suite expects the analytics microservice to be importable from the
``services`` package.  The actual implementation lives in
``yosai_intel_dashboard.src.services.analytics_microservice``.  This module
re-exports the FastAPI ``app`` object from the real implementation so that both
import locations behave the same.
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
