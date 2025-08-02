"""Utilities for test-time module import handling.

These helpers provide a central place for creating and registering lightweight
stub modules used across the test-suite.  They avoid repetitive manual
`sys.modules` manipulation in individual tests.
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from types import ModuleType
from typing import Any

from optional_dependencies import register_stub


def simple_module(name: str, **attrs: Any) -> ModuleType:
    """Return a new :class:`ModuleType` with *attrs* set."""
    mod = ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    return mod


def install_stub(name: str, module: ModuleType) -> ModuleType:
    """Register *module* as a stub and expose it via :data:`sys.modules`."""
    sys.modules.setdefault(name, module)
    register_stub(name, module)
    return module


def simple_stub(name: str, **attrs: Any) -> ModuleType:
    """Convenience wrapper combining :func:`simple_module` and :func:`install_stub`."""
    mod = simple_module(name, **attrs)
    return install_stub(name, mod)


@contextmanager
def temp_module(name: str, **attrs: Any) -> ModuleType:
    """Temporarily register a stub module.

    The module is registered and added to :data:`sys.modules` for the duration of
    the context, then removed afterwards.
    """
    mod = simple_stub(name, **attrs)
    try:
        yield mod
    finally:  # pragma: no cover - cleanup
        sys.modules.pop(name, None)


__all__ = [
    "install_stub",
    "simple_module",
    "simple_stub",
    "temp_module",
    "register_stub",
]
