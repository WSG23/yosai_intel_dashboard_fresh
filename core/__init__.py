"""Core package exports and typing utilities."""

from typing import TYPE_CHECKING, Any

from .advanced_query_optimizer import AdvancedQueryOptimizer
from .async_utils import (
    AsyncContextManager,
    CircuitBreaker,
    CircuitBreakerOpen,
    async_batch,
    async_retry,
    circuit_breaker,
)
from .base_database_service import BaseDatabaseService
from .base_model import BaseModel
from .cache_manager import (
    CacheConfig,
    InMemoryCacheManager,
    RedisCacheManager,
    cache_with_lock,
)
from .cache_warmer import IntelligentCacheWarmer
from .callback_modules import CallbackModule, CallbackModuleRegistry
from .cpu_optimizer import CPUOptimizer
from .deprecation import deprecated
from .hierarchical_cache_manager import HierarchicalCacheManager
from .intelligent_multilevel_cache import (
    IntelligentMultiLevelCache,
    create_intelligent_cache_manager,
)
from .memory_manager import MemoryManager
from .truly_unified_callbacks import TrulyUnifiedCallbacks
from .base_database_service import BaseDatabaseService
from .deprecation import deprecated
from .di_decorators import injectable, inject
from .env_validation import validate_env


if TYPE_CHECKING:  # pragma: no cover - type hints only
    from .truly_unified_callbacks import (
        TrulyUnifiedCallbacks as TrulyUnifiedCallbacksType,
    )
else:  # pragma: no cover - fallback at runtime
    TrulyUnifiedCallbacksType = Any  # type: ignore[misc]

__all__ = [
    "TrulyUnifiedCallbacks",
    "TrulyUnifiedCallbacksType",
    "CacheConfig",
    "InMemoryCacheManager",
    "RedisCacheManager",
    "cache_with_lock",
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
    "BaseDatabaseService",
    "deprecated",
    "injectable",
    "inject",
    "validate_env",

]
