"""Lazy loader for :mod:`yosai_intel_dashboard.src.adapters.api`."""

from __future__ import annotations

import importlib
from importlib import machinery, util
from types import ModuleType

_TARGET = "yosai_intel_dashboard.src.adapters.api"

_spec = util.find_spec(_TARGET)
if _spec is None:  # pragma: no cover - underlying package missing
    raise ImportError(f"Cannot find {_TARGET}")

__path__ = list(_spec.submodule_search_locations or [])
__spec__ = machinery.ModuleSpec(
    __name__, loader=None, origin=_spec.origin, is_package=True
)
__spec__.submodule_search_locations = __path__

_module: ModuleType | None = None


def _load() -> ModuleType:
    global _module
    if _module is None:
        _module = importlib.import_module(_TARGET)
        globals().update(_module.__dict__)
    return _module


def __getattr__(name: str):
    return getattr(_load(), name)


def __dir__() -> list[str]:  # pragma: no cover - trivial
    return sorted(set(globals()) | set(dir(_load())))
