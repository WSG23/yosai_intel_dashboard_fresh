"""Core package exports and typing utilities.

This simplified module provides lazy access to heavy submodules so that tests
can import ``yosai_intel_dashboard.src.core`` without pulling in optional
runtime dependencies.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .registry import ServiceRegistry, registry

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
    from .deprecation import deprecated
    from .base_model import BaseModel
    from .cache_warmer import IntelligentCacheWarmer
    from .callback_modules import CallbackModule, CallbackModuleRegistry
    from .cpu_optimizer import CPUOptimizer
    from .env_validation import validate_env
    from .hierarchical_cache_manager import (
        HierarchicalCacheConfig,
        HierarchicalCacheManager,
    )
    from .intelligent_multilevel_cache import (
        IntelligentMultiLevelCache,
        create_intelligent_cache_manager,
    )
    from .memory_manager import MemoryManager
    from .di_decorators import inject, injectable
else:  # pragma: no cover - fallbacks at runtime
    AsyncContextManager = Any  # type: ignore[misc]
    CircuitBreaker = Any  # type: ignore[misc]
    CircuitBreakerOpen = Any  # type: ignore[misc]
    async_batch = Any  # type: ignore[misc]
    async_retry = Any  # type: ignore[misc]
    circuit_breaker = Any  # type: ignore[misc]
    CacheConfig = Any  # type: ignore[misc]
    InMemoryCacheManager = Any  # type: ignore[misc]
    RedisCacheManager = Any  # type: ignore[misc]
    cache_with_lock = Any  # type: ignore[misc]
    TrulyUnifiedCallbacks = Any  # type: ignore[misc]
    BaseDatabaseService = Any  # type: ignore[misc]
    deprecated = Any  # type: ignore[misc]
    BaseModel = Any  # type: ignore[misc]
    IntelligentCacheWarmer = Any  # type: ignore[misc]
    CallbackModule = Any  # type: ignore[misc]
    CallbackModuleRegistry = Any  # type: ignore[misc]
    CPUOptimizer = Any  # type: ignore[misc]
    validate_env = Any  # type: ignore[misc]
    HierarchicalCacheConfig = Any  # type: ignore[misc]
    HierarchicalCacheManager = Any  # type: ignore[misc]
    IntelligentMultiLevelCache = Any  # type: ignore[misc]
    create_intelligent_cache_manager = Any  # type: ignore[misc]
    MemoryManager = Any  # type: ignore[misc]
    inject = Any  # type: ignore[misc]
    injectable = Any  # type: ignore[misc]

__all__ = [
    "TrulyUnifiedCallbacks",
    "TrulyUnifiedCallbacksType",
    "CacheConfig",
    "InMemoryCacheManager",
    "RedisCacheManager",
    "cache_with_lock",
    "AdvancedQueryOptimizer",
    "HierarchicalCacheManager",
    "HierarchicalCacheConfig",
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
    "ServiceRegistry",
    "registry",
]

_ASYNC_EXPORTS = {
    "AsyncContextManager",
    "CircuitBreaker",
    "CircuitBreakerOpen",
    "async_batch",
    "async_retry",
    "circuit_breaker",
}

_LAZY_EXPORTS = {
    "TrulyUnifiedCallbacks": (
        "..infrastructure.callbacks.unified_callbacks",
        "TrulyUnifiedCallbacks",
    ),
    "CacheConfig": ("..infrastructure.cache.cache_manager", "CacheConfig"),
    "InMemoryCacheManager": (
        "..infrastructure.cache.cache_manager",
        "InMemoryCacheManager",
    ),
    "RedisCacheManager": (
        "..infrastructure.cache.cache_manager",
        "RedisCacheManager",
    ),
    "cache_with_lock": ("..infrastructure.cache.cache_manager", "cache_with_lock"),
    "BaseDatabaseService": (".base_database_service", "BaseDatabaseService"),
    "deprecated": (".deprecation", "deprecated"),
    "AdvancedQueryOptimizer": (".advanced_query_optimizer", "AdvancedQueryOptimizer"),
    "HierarchicalCacheManager": (".hierarchical_cache_manager", "HierarchicalCacheManager"),
    "HierarchicalCacheConfig": (".hierarchical_cache_manager", "HierarchicalCacheConfig"),
    "IntelligentCacheWarmer": (".cache_warmer", "IntelligentCacheWarmer"),
    "MemoryManager": (".memory_manager", "MemoryManager"),
    "CPUOptimizer": (".cpu_optimizer", "CPUOptimizer"),

    "IntelligentMultiLevelCache": (
        ".intelligent_multilevel_cache",
        "IntelligentMultiLevelCache",
    ),
    "create_intelligent_cache_manager": (
        ".intelligent_multilevel_cache",
        "create_intelligent_cache_manager",
    ),
    "CallbackModule": (".callback_modules", "CallbackModule"),
    "CallbackModuleRegistry": (".callback_modules", "CallbackModuleRegistry"),
    "BaseModel": (".base_model", "BaseModel"),
    "inject": (".di_decorators", "inject"),
    "injectable": (".di_decorators", "injectable"),
    "validate_env": (".env_validation", "validate_env"),

}


def __getattr__(name: str) -> Any:
    if name in _ASYNC_EXPORTS:
        from . import async_utils

        value = getattr(async_utils, name)
        globals()[name] = value
        return value
    if name in _LAZY_EXPORTS:
        module_name, attr_name = _LAZY_EXPORTS[name]
        module = import_module(module_name, __package__)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(name)
