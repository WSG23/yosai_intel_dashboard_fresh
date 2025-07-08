"""Deprecated compatibility wrapper for :mod:`core.unicode`."""
from __future__ import annotations

import warnings

from .unicode import *  # noqa: F401,F403

warnings.warn(
    "core.unicode_processor is deprecated; use core.unicode instead",
    DeprecationWarning,
    stacklevel=2,
)
