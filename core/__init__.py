"""Core package exports and typing utilities."""

from typing import TYPE_CHECKING, Any

from .truly_unified_callbacks import TrulyUnifiedCallbacks

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from .truly_unified_callbacks import (
        TrulyUnifiedCallbacks as TrulyUnifiedCallbacksType,
    )
else:  # pragma: no cover - fallback at runtime
    TrulyUnifiedCallbacksType = Any  # type: ignore[misc]

__all__ = ["TrulyUnifiedCallbacks", "TrulyUnifiedCallbacksType"]

