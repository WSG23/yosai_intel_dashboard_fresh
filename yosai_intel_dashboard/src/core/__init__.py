"""Core package exports and typing utilities."""

from typing import TYPE_CHECKING, Any

from .advanced_query_optimizer import AdvancedQueryOptimizer

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from .async_utils import (
        AsyncContextManager,
        CircuitBreaker,
        CircuitBreakerOpen,
        async_batch,
        async_retry,
        circuit_breaker,
    )

from ..infrastructure.cache.cache_manager import (
    CacheConfig,
    InMemoryCacheManager,
    RedisCacheManager,
    cache_with_lock,
)
from ..infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from .base_database_service import BaseDatabaseService
from .base_model import BaseModel
from .cache_warmer import IntelligentCacheWarmer
from .callback_modules import CallbackModule, CallbackModuleRegistry
from .cpu_optimizer import CPUOptimizer
from .deprecation import deprecated
from .di_decorators import inject, injectable
from .env_validation import validate_env
from .hierarchical_cache_manager import HierarchicalCacheManager
from .intelligent_multilevel_cache import (
    IntelligentMultiLevelCache,
    create_intelligent_cache_manager,
)
from .memory_manager import MemoryManager

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from ..infrastructure.callbacks.unified_callbacks import (
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
    "AsyncContextManager",
    "async_retry",
    "CircuitBreaker",
    "CircuitBreakerOpen",
    "circuit_breaker",
    "async_batch",
]


_ASYNC_EXPORTS = {
    "AsyncContextManager",
    "CircuitBreaker",
    "CircuitBreakerOpen",
    "async_batch",
    "async_retry",
    "circuit_breaker",
}


def __getattr__(name: str) -> Any:
    if name in _ASYNC_EXPORTS:
        from . import async_utils

        value = getattr(async_utils, name)
        globals()[name] = value
        return value
    raise AttributeError(name)
