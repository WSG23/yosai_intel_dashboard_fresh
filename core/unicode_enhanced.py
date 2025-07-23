"""Deprecated compatibility layer for :mod:`core.unicode`."""

from __future__ import annotations

import warnings

from .unicode import (
    EnhancedUnicodeProcessor,
    SurrogateHandlingConfig,
    SurrogateHandlingStrategy,
)

warnings.warn(
    "core.unicode_enhanced is deprecated; use core.unicode instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "EnhancedUnicodeProcessor",
    "SurrogateHandlingConfig",
    "SurrogateHandlingStrategy",
]
