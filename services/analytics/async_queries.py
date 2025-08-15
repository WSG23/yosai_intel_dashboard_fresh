"""Re-export async query helpers for the analytics service."""

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - used for type checking only
    from yosai_intel_dashboard.src.services.analytics_microservice import async_queries as _impl
else:  # pragma: no cover - runtime import only
    _impl = import_module("yosai_intel_dashboard.src.services.analytics_microservice.async_queries")

# Re-export public names from implementation module
for _name in dir(_impl):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_impl, _name)

__all__ = [name for name in dir(_impl) if not name.startswith("_")]
