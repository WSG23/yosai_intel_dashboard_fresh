"""Utility helpers for importing optional dependencies.

This module centralises logic for importing optional dependencies across the
project.  The :class:`ImportResolver` performs imports with caching and can
produce stub modules when the real dependency is missing.  Missing imports are
tracked via :mod:`monitoring.missing_dependencies` so that the impact can be
observed in metrics.

Convenience functions :func:`safe_import` and :func:`register_fallback` are
exposed along with a global :data:`resolver` instance for project wide use.
"""

from __future__ import annotations

import importlib
import types
from typing import Any, Callable, Dict, Set

from monitoring.missing_dependencies import missing_dependencies

StubFactory = Callable[[], Any] | Any


class ImportResolver:
    """Resolver capable of importing modules with fallbacks.

    The resolver caches resolved modules and allows registering fallback
    factories that return lightweight stand‑ins when an import fails.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}
        self._fallbacks: Dict[str, StubFactory] = {}
        self._missing: Set[str] = set()

    # ------------------------------------------------------------------
    # Fallback registration
    def register(self, name: str, factory: StubFactory) -> None:
        """Register ``factory`` as a fallback for ``name``."""

        self._fallbacks[name] = factory

    # ------------------------------------------------------------------
    # Import resolution
    def resolve(self, name: str, default: StubFactory | None = None) -> Any:
        """Return ``name`` or a fallback if the import fails.

        Parameters
        ----------
        name:
            Dotted module path or ``pkg.mod:attr`` style reference.
        default:
            Optional factory overriding registered fallbacks.
        """

        if name in self._cache:
            return self._cache[name]

        module_name, attr = name, None
        if "." in name:
            module_name, attr = name.rsplit(".", 1)
        try:
            module = importlib.import_module(module_name)
            value = getattr(module, attr) if attr else module
            self._cache[name] = value
            return value
        except ModuleNotFoundError:
            factory = (
                default or self._fallbacks.get(name) or self._fallbacks.get(module_name)
            )
            if factory is None:
                raise
            missing_dependencies.labels(dependency=name).inc()
            self._missing.add(name)
            value = factory() if callable(factory) else factory
            self._cache[name] = value
            return value

    # ------------------------------------------------------------------
    @property
    def missing(self) -> Set[str]:
        """Names of dependencies that could not be imported."""

        return set(self._missing)


# ---------------------------------------------------------------------------
# Convenience layer
resolver = ImportResolver()


def register_fallback(name: str, factory: StubFactory) -> None:
    """Register ``factory`` as a fallback for ``name`` on the global resolver."""

    resolver.register(name, factory)


def safe_import(name: str, stub_factory: StubFactory | None = None) -> Any:
    """Safely import ``name`` returning a stub when unavailable."""

    return resolver.resolve(name, stub_factory)


__all__ = ["ImportResolver", "safe_import", "register_fallback", "resolver"]


# ---------------------------------------------------------------------------
# Default stubs for common heavy dependencies


def _simple_module(name: str, **attrs: Any) -> types.ModuleType:
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


# Dash and related packages --------------------------------------------------
_dash = _simple_module("dash")
_dash.html = _simple_module("dash.html")
_dash.dcc = _simple_module("dash.dcc")
_dash.dependencies = _simple_module("dash.dependencies")
_dash._callback = _simple_module("dash._callback")
for _name, _factory in {
    "dash": lambda: _dash,
    "dash.html": lambda: _dash.html,
    "dash.dcc": lambda: _dash.dcc,
    "dash.dependencies": lambda: _dash.dependencies,
    "dash._callback": lambda: _dash._callback,
}.items():
    register_fallback(_name, _factory)


# pandas ---------------------------------------------------------------------
register_fallback("pandas", lambda: _simple_module("pandas", DataFrame=object))


# numpy ----------------------------------------------------------------------
register_fallback(
    "numpy",
    lambda: _simple_module("numpy", array=lambda *a, **k: [], ndarray=object),
)


# scikit-learn ---------------------------------------------------------------
_sklearn = _simple_module("sklearn")
_sklearn.base = _simple_module("sklearn.base", BaseEstimator=object)
register_fallback("sklearn", lambda: _sklearn)
register_fallback("sklearn.base", lambda: _sklearn.base)
