"""Backward-compatible wrapper for environment overrides."""

from __future__ import annotations

from typing import Any

from .environment_processor import EnvironmentProcessor


def apply_env_overrides(config: Any) -> None:
    """Apply environment variable overrides using :class:`EnvironmentProcessor`."""

    processor = EnvironmentProcessor()
    processor.apply(config)


__all__ = ["apply_env_overrides"]
