"""Compatibility exports for configuration dataclasses and mixins."""

from __future__ import annotations

from .configuration_mixin import ConfigurationMixin

__all__ = [
    "ConfigurationMixin",
    "AppConfig",
    "DatabaseConfig",
    "SecurityConfig",
    "SampleFilesConfig",
    "AnalyticsConfig",
    "MonitoringConfig",
    "RetrainingConfig",
    "CacheConfig",
    "SecretValidationConfig",
    "Config",
]


def __getattr__(name: str):
    module = __import__(
        "yosai_intel_dashboard.src.infrastructure.config.base", fromlist=[name]
    )
    value = getattr(module, name)
    globals()[name] = value
    return value
