"""Deprecated wrapper for :mod:`validation.security_validator`."""
from __future__ import annotations

from warnings import warn

from validation.security_validator import SecurityValidator as _SecurityValidator

warn(
    "core.security_validator.SecurityValidator is deprecated; "
    "use validation.security_validator.SecurityValidator instead",
    DeprecationWarning,
    stacklevel=2,
)

SecurityValidator = _SecurityValidator

__all__ = ["SecurityValidator"]
