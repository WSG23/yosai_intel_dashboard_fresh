"""Core package exports and typing utilities."""

from typing import TYPE_CHECKING, Any

from .truly_unified_callbacks import TrulyUnifiedCallbacks
from .advanced_cache import (
    AdvancedCacheManager,
    create_advanced_cache_manager,
    cache_with_lock,
)

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from .truly_unified_callbacks import (
        TrulyUnifiedCallbacks as TrulyUnifiedCallbacksType,
    )
else:  # pragma: no cover - fallback at runtime
    TrulyUnifiedCallbacksType = Any  # type: ignore[misc]

__all__ = [
    "TrulyUnifiedCallbacks",
    "TrulyUnifiedCallbacksType",
    "AdvancedCacheManager",
    "cache_with_lock",
    "create_advanced_cache_manager",
]
