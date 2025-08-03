"""Backward-compatible wrapper for environment overrides."""

from __future__ import annotations

from typing import Any
import warnings

from .environment_processor import EnvironmentProcessor


def apply_env_overrides(config: Any) -> None:
    """Apply environment variable overrides using :class:`EnvironmentProcessor`.

    Deprecated: use :class:`EnvironmentProcessor` directly.
    """

    warnings.warn(
        "apply_env_overrides is deprecated; use EnvironmentProcessor().apply",
        DeprecationWarning,
        stacklevel=2,
    )
    processor = EnvironmentProcessor()
    processor.apply(config)


__all__ = ["apply_env_overrides"]
