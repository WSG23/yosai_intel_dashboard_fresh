"""Utility helpers for importing modules in tests.

This module provides two helpers: :func:`safe_import` and
:func:`import_optional`.  Both functions use the standard import
machinery and avoid direct interaction with ``sys.modules`` so they can
be used in tests without the side effects of manual module patching.

Example
-------
Instead of manually inserting stubs into ``sys.modules``:

>>> import sys
>>> sys.modules['myservice'] = object()  # doctest: +SKIP
>>> import myservice  # doctest: +SKIP

You can use ``safe_import`` to produce a stub only when the module is
missing:

>>> from types import SimpleNamespace
>>> stub = SimpleNamespace(api=lambda: 'ok')
>>> service = safe_import('myservice', lambda: stub)
>>> service.api()
'ok'

Optional dependencies can be imported with a predefined stub using
:func:`import_optional`:

>>> fake_redis = SimpleNamespace(get=lambda k: None)
>>> redis = import_optional('redis', fake_redis)
>>> redis.get('foo')

The module also exposes small protocol based doubles that can be used to
stand‑in for common interfaces like HTTP clients and cache backends in a
lightweight fashion.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, Protocol, Optional, Dict, List, Tuple


T = Any
StubFactory = Callable[[], T]


def safe_import(module_name: str, stub_factory: StubFactory | None = None) -> T:
    """Safely import ``module_name`` or create a stub.

    Parameters
    ----------
    module_name:
        Name of the module to import.
    stub_factory:
        Optional callable used to create and return a stub when the module
        cannot be imported.  If omitted, :class:`ModuleNotFoundError` is
        propagated to the caller.

    Returns
    -------
    The imported module or a stub generated by ``stub_factory``.
    """
    try:
        return import_module(module_name)
    except ModuleNotFoundError:
        if stub_factory is None:
            raise
        return stub_factory()


def import_optional(module_name: str, default_stub: T) -> T:
    """Import ``module_name`` returning ``default_stub`` if not available."""
    return safe_import(module_name, lambda: default_stub)


class HTTPClient(Protocol):
    """Protocol describing the minimal HTTP client interface used in tests."""

    def get(self, url: str, **kwargs: Any) -> Any:
        ...

    def post(self, url: str, data: Any | None = None, **kwargs: Any) -> Any:
        ...


class HTTPClientDouble(HTTPClient):
    """A lightweight double that records HTTP requests made against it."""

    def __init__(self) -> None:
        self.requests: List[Tuple[str, str, Dict[str, Any]]] = []

    def get(self, url: str, **kwargs: Any) -> Any:
        self.requests.append(("GET", url, kwargs))
        return kwargs.get("return_value")

    def post(self, url: str, data: Any | None = None, **kwargs: Any) -> Any:
        kwargs = dict(kwargs)
        if data is not None:
            kwargs["data"] = data
        self.requests.append(("POST", url, kwargs))
        return kwargs.get("return_value")


class CacheBackend(Protocol):
    """Protocol for a simple cache backend."""

    def get(self, key: str) -> Any:
        ...

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ...

    def delete(self, key: str) -> None:
        ...


class CacheBackendDouble(CacheBackend):
    """In‑memory cache backend suitable for tests."""

    def __init__(self) -> None:
        self.storage: Dict[str, Any] = {}

    def get(self, key: str) -> Any:
        return self.storage.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self.storage[key] = value

    def delete(self, key: str) -> None:
        self.storage.pop(key, None)


__all__ = [
    "safe_import",
    "import_optional",
    "HTTPClient",
    "HTTPClientDouble",
    "CacheBackend",
    "CacheBackendDouble",

]
