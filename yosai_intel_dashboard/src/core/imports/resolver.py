"""Utilities for safely importing optional dependencies.

This module exposes :func:`safe_import` which attempts to import a module by
name and falls back to a registered stub when the module is missing.  Fallbacks
may be registered via :func:`register_fallback` or provided inline using the
``stub_factory`` argument for backwards compatibility.

"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any, Callable, Dict
import sys

StubFactory = Callable[[], ModuleType]

_fallbacks: Dict[str, StubFactory] = {}


def register_fallback(module_name: str, factory: StubFactory) -> None:
    """Register a fallback ``factory`` for ``module_name``.

    The factory will be invoked if ``module_name`` cannot be imported via the
    normal Python import machinery.  The resulting stub is inserted into
    ``sys.modules`` so subsequent imports resolve to the same object.
    """

    _fallbacks[module_name] = factory


def safe_import(module_name: str, stub_factory: StubFactory | None = None) -> Any:
    """Import ``module_name`` using any registered fallbacks.

    Parameters
    ----------
    module_name:
        The fully qualified name of the module to import.
    stub_factory:
        Optional callable used to create a stub when the import fails.  This is
        retained for backwards compatibility with older tests; new code should
        prefer :func:`register_fallback`.
    """

    if module_name in sys.modules:
        return sys.modules[module_name]
    if isinstance(stub_factory, ModuleType):
        sys.modules.setdefault(module_name, stub_factory)
        return stub_factory
    try:
        return import_module(module_name)
    except ModuleNotFoundError:
        factory = stub_factory or _fallbacks.get(module_name)
        if factory is None:
            raise
        stub = factory() if callable(factory) else factory
        if isinstance(stub, ModuleType):
            sys.modules.setdefault(module_name, stub)
        return stub


__all__ = ["safe_import", "register_fallback"]

