from __future__ import annotations

"""Deprecated: use :mod:`core.unicode` instead."""

import warnings
from typing import Any

from .unicode import safe_unicode_decode as _safe_unicode_decode

warnings.warn(
    "core.unicode_decode is deprecated; use core.unicode.safe_unicode_decode",
    DeprecationWarning,
    stacklevel=2,
)


def safe_unicode_decode(data: Any, encoding: str = "utf-8") -> str:
    return _safe_unicode_decode(data, encoding)


__all__ = ["safe_unicode_decode"]
