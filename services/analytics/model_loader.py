"""Provide access to model loading helpers used by analytics tests."""

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from yosai_intel_dashboard.src.services.analytics_microservice import model_loader as _impl
else:  # pragma: no cover - runtime import only
    _impl = import_module("yosai_intel_dashboard.src.services.analytics_microservice.model_loader")

for _name in dir(_impl):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_impl, _name)

__all__ = [name for name in dir(_impl) if not name.startswith("_")]
