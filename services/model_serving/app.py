"""Compatibility wrapper for the model serving microservice.

The production implementation lives under ``yosai_intel_dashboard.src`` but the
unit tests import the application from the ``services`` package.  This module
re-exports the FastAPI ``app`` object from the real implementation so both
locations behave the same.
"""

from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    _mod: ModuleType
else:  # pragma: no cover - runtime import only
    _mod = import_module("yosai_intel_dashboard.src.services.model_serving.app")

app = cast(object, getattr(_mod, "app"))

__all__ = ["app"]
