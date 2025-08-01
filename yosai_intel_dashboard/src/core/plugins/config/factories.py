"""Factory classes for creating configuration components"""

import logging
from typing import Any, Callable, Dict, List, Type

from yosai_intel_dashboard.src.core.intelligent_multilevel_cache import IntelligentMultiLevelCache

from .interfaces import ICacheManager, IDatabaseManager

logger = logging.getLogger(__name__)


class DatabaseManagerFactory:
    """Factory for creating database managers"""

    _managers: Dict[str, Type[IDatabaseManager]] = {}

    @classmethod
    def register_manager(
        cls, db_type: str, manager_class: Type[IDatabaseManager]
    ) -> None:
        """Register a new database manager type"""
        cls._managers[db_type] = manager_class
        logger.info(f"Registered database manager: {db_type}")

    @classmethod
    def create_manager(cls, database_config) -> IDatabaseManager:
        """Create database manager based on configuration"""
        # Import here to avoid circular imports
        from .database_manager import (
            AsyncPostgreSQLManager,
            SQLiteDatabaseManager,
        )

        # Register default managers if not already registered
        if not cls._managers:
            cls._managers.update(
                {
                    "postgresql": AsyncPostgreSQLManager,
                    "sqlite": SQLiteDatabaseManager,
                }
            )

        db_type = getattr(database_config, "type", "sqlite")

        if db_type not in cls._managers:
            logger.warning(f"Unknown database type: {db_type}, using sqlite")
            db_type = "sqlite"

        manager_class = cls._managers[db_type]
        return manager_class(database_config)

    @classmethod
    def get_available_types(cls) -> List[str]:
        """Get list of available database types"""
        return list(cls._managers.keys())


class CacheManagerFactory:
    """Factory for creating cache managers"""

    _managers: Dict[str, Type[ICacheManager]] = {}

    @classmethod
    def register_manager(
        cls, cache_type: str, manager_class: Type[ICacheManager]
    ) -> None:
        """Register a new cache manager type"""
        cls._managers[cache_type] = manager_class
        logger.info(f"Registered cache manager: {cache_type}")

    @classmethod
    def create_manager(cls, cache_config) -> ICacheManager:
        """Create cache manager based on configuration"""
        # Import here to avoid circular imports
        from .cache_manager import (
            AdvancedRedisCacheManager,
            MemoryCacheManager,
            RedisCacheManager,
        )

        # Register default managers if not already registered
        if not cls._managers:
            cls._managers.update(
                {
                    "memory": MemoryCacheManager,
                    "redis": RedisCacheManager,
                    "advanced_redis": AdvancedRedisCacheManager,
                    "intelligent": IntelligentMultiLevelCache,
                }
            )

        cache_type = getattr(cache_config, "type", "memory")

        if cache_type not in cls._managers:
            logger.warning(f"Unknown cache type: {cache_type}, using memory")
            cache_type = "memory"

        manager_class = cls._managers[cache_type]
        return manager_class(cache_config)

    @classmethod
    def get_available_types(cls) -> List[str]:
        """Get list of available cache types"""
        return list(cls._managers.keys())
