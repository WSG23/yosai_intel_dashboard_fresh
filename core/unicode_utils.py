"""Deprecated compatibility layer for :mod:`core.unicode`."""

from __future__ import annotations

import warnings
from typing import Any

from .unicode import (
    UnicodeNormalizationError,
    normalize_unicode_safely,
    detect_surrogate_pairs,
    sanitize_for_utf8,
)

warnings.warn(
    "core.unicode_utils is deprecated; use core.unicode instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "normalize_unicode_safely",
    "detect_surrogate_pairs",
    "sanitize_for_utf8",
    "UnicodeNormalizationError",
]
