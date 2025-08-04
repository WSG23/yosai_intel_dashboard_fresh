from __future__ import annotations

"""Lightweight configuration service.

The :class:`ConfigService` loads configuration values from the environment
(or a provided mapping) and exposes them as read‑only properties.  It acts as a
central place for runtime settings used by small demo components within the
``src`` package.  Instances are immutable which prevents accidental mutation of
settings during tests.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Protocol
import os

from yosai_intel_dashboard.src.infrastructure.config.configuration_mixin import (
    ConfigurationMixin,
)


class ConfigProvider(Protocol):
    """Protocol describing the configuration attributes used by components."""

    @property
    def metrics_interval(self) -> float: ...

    @property
    def ping_interval(self) -> float: ...

    @property
    def ping_timeout(self) -> float: ...

    @property
    def ai_confidence_threshold(self) -> float: ...

    def get_ai_confidence_threshold(self) -> float: ...

    @property
    def max_upload_size_mb(self) -> int: ...

    def get_max_upload_size_mb(self) -> int: ...

    @property
    def upload_chunk_size(self) -> int: ...

    def get_upload_chunk_size(self) -> int: ...


@dataclass(frozen=True)
class ConfigService(ConfigurationMixin, ConfigProvider):
    """Simple immutable configuration container."""

    _settings: Mapping[str, Any]

    def __init__(self, settings: Mapping[str, Any] | None = None) -> None:
        defaults = {
            "metrics_interval": float(os.getenv("METRICS_INTERVAL", "1.0")),
            "ping_interval": float(os.getenv("PING_INTERVAL", "30.0")),
            "ping_timeout": float(os.getenv("PING_TIMEOUT", "10.0")),
            "ai_confidence_threshold": float(
                os.getenv("AI_CONFIDENCE_THRESHOLD", "0.8")
            ),
            "max_upload_size_mb": int(os.getenv("MAX_UPLOAD_SIZE_MB", "100")),
            "upload_chunk_size": int(os.getenv("UPLOAD_CHUNK_SIZE", "50000")),
        }
        if settings:
            defaults.update(settings)
        object.__setattr__(self, "_settings", MappingProxyType(dict(defaults)))

    # Expose settings via properties for convenient, type‑checked access
    @property
    def metrics_interval(self) -> float:
        return float(self._settings["metrics_interval"])

    @property
    def ping_interval(self) -> float:
        return float(self._settings["ping_interval"])

    @property
    def ping_timeout(self) -> float:
        return float(self._settings["ping_timeout"])

    @property
    def ai_confidence_threshold(self) -> float:
        return float(self._settings["ai_confidence_threshold"])

    @property
    def max_upload_size_mb(self) -> int:
        return int(self._settings["max_upload_size_mb"])

    @property
    def upload_chunk_size(self) -> int:
        return int(self._settings["upload_chunk_size"])


__all__ = ["ConfigService", "ConfigProvider"]
