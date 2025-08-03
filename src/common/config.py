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


class ConfigProvider(Protocol):
    """Protocol describing the configuration attributes used by components."""

    @property
    def metrics_interval(self) -> float: ...

    @property
    def ping_interval(self) -> float: ...

    @property
    def ping_timeout(self) -> float: ...


@dataclass(frozen=True)
class ConfigService(ConfigProvider):
    """Simple immutable configuration container."""

    _settings: Mapping[str, Any]

    def __init__(self, settings: Mapping[str, Any] | None = None) -> None:
        if settings is None:
            settings = {
                "metrics_interval": float(os.getenv("METRICS_INTERVAL", "1.0")),
                "ping_interval": float(os.getenv("PING_INTERVAL", "30.0")),
                "ping_timeout": float(os.getenv("PING_TIMEOUT", "10.0")),
            }
        object.__setattr__(self, "_settings", MappingProxyType(dict(settings)))

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


__all__ = ["ConfigService", "ConfigProvider"]
