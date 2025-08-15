"""Re-export the analytics service used by the FastAPI app."""

from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from yosai_intel_dashboard.src.services.analytics_microservice import analytics_service as _impl
else:  # pragma: no cover - runtime import only
    _impl = import_module("yosai_intel_dashboard.src.services.analytics_microservice.analytics_service")

# Expose all public attributes from the implementation module
for _name in dir(_impl):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_impl, _name)

__all__ = [name for name in dir(_impl) if not name.startswith("_")]
