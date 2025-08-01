"""Core interfaces and protocols."""

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .protocols import (
    ConfigurationProviderProtocol,
    AnalyticsProviderProtocol,
    ConfigProviderProtocol,
)
# Service protocol imports are deferred to avoid heavy dependencies

if TYPE_CHECKING:  # pragma: no cover - only for static typing
    from yosai_intel_dashboard.src.core.protocols import UnicodeProcessorProtocol
else:  # pragma: no cover - runtime lazy import
    UnicodeProcessorProtocol = Any  # type: ignore[misc]

__all__ = [
    "UnicodeProcessorProtocol",
    "ConfigurationProviderProtocol",
    "AnalyticsProviderProtocol",
    "ConfigProviderProtocol",
    "UploadValidatorProtocol",
    "ExportServiceProtocol",
    "DoorMappingServiceProtocol",
    "DeviceLearningServiceProtocol",
    "UploadDataStoreProtocol",
    "UploadDataServiceProtocol",
    "MappingServiceProtocol",
    "AnalyticsDataLoaderProtocol",
    "DatabaseAnalyticsRetrieverProtocol",
]


_LAZY_MODULE = "yosai_intel_dashboard.src.core.protocols"
_SERVICE_MODULE = "yosai_intel_dashboard.src.core.interfaces.service_protocols"


def __getattr__(name: str) -> Any:
    if name == "UnicodeProcessorProtocol" or not globals().get(name):
        module = import_module(_LAZY_MODULE)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    if name in {
        "UploadValidatorProtocol",
        "ExportServiceProtocol",
        "DoorMappingServiceProtocol",
        "DeviceLearningServiceProtocol",
        "UploadDataStoreProtocol",
        "UploadDataServiceProtocol",
        "MappingServiceProtocol",
        "AnalyticsDataLoaderProtocol",
        "DatabaseAnalyticsRetrieverProtocol",
    }:
        module = import_module(_SERVICE_MODULE)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(name)
