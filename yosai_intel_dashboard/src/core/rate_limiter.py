"""Compatibility shim for :mod:`core.rate_limiter`.

This module is deprecated in favor of :mod:`core.security`.
It re-exports :class:`RateLimiter` and :func:`create_rate_limiter` from the
new location and emits a :class:`DeprecationWarning` when imported.
"""

from __future__ import annotations

import warnings

from .security import RateLimiter, create_rate_limiter

warnings.warn(
    "core.rate_limiter is deprecated; use core.security instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["RateLimiter", "create_rate_limiter"]

