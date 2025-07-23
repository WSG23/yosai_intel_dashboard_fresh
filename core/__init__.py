"""Core package exports and typing utilities."""

from typing import TYPE_CHECKING, Any

from .advanced_cache import (
    AdvancedCacheManager,
    cache_with_lock,
    create_advanced_cache_manager,
)
from .advanced_query_optimizer import AdvancedQueryOptimizer
from .base_model import BaseModel
from .cache_warmer import IntelligentCacheWarmer
from .callback_modules import CallbackModule, CallbackModuleRegistry
from .cpu_optimizer import CPUOptimizer
from .hierarchical_cache_manager import HierarchicalCacheManager
from .intelligent_multilevel_cache import (
    IntelligentMultiLevelCache,
    create_intelligent_cache_manager,
)
from .memory_manager import MemoryManager
from .truly_unified_callbacks import TrulyUnifiedCallbacks

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
    "AdvancedQueryOptimizer",
    "HierarchicalCacheManager",
    "IntelligentCacheWarmer",
    "MemoryManager",
    "CPUOptimizer",
    "IntelligentMultiLevelCache",
    "create_intelligent_cache_manager",
    "CallbackModule",
    "CallbackModuleRegistry",
    "BaseModel",
]
