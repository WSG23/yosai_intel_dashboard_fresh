from __future__ import annotations

"""Shared helpers for validation utilities."""

from typing import Any


def _lazy_string_validator() -> Any:
    """Load :class:`SecurityValidator` lazily to avoid heavy imports."""
    from validation.security_validator import SecurityValidator as StringValidator

    return StringValidator()


__all__ = ["_lazy_string_validator"]
