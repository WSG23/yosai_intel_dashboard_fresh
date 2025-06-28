"""Factory classes for creating configuration components"""

import logging
from typing import Type, Dict, Callable, Any, List
from .interfaces import IDatabaseManager, ICacheManager

logger = logging.getLogger(__name__)

class DatabaseManagerFactory:
    """Factory for creating database managers"""

    _managers: Dict[str, Type[IDatabaseManager]] = {}

    @classmethod
    def register_manager(cls, db_type: str, manager_class: Type[IDatabaseManager]) -> None:
        """Register a new database manager type"""
        cls._managers[db_type] = manager_class
        logger.info(f"Registered database manager: {db_type}")

    @classmethod
    def create_manager(cls, database_config) -> IDatabaseManager:
        """Create database manager based on configuration"""
        # Import here to avoid circular imports
        from .database_manager import MockDatabaseManager, PostgreSQLDatabaseManager, SQLiteDatabaseManager

        # Register default managers if not already registered
        if not cls._managers:
            cls._managers.update({
                'mock': MockDatabaseManager,
                'postgresql': PostgreSQLDatabaseManager,
                'sqlite': SQLiteDatabaseManager,
            })

        db_type = getattr(database_config, 'type', 'mock')

        if db_type not in cls._managers:
            logger.warning(f"Unknown database type: {db_type}, using mock")
            db_type = 'mock'

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
    def register_manager(cls, cache_type: str, manager_class: Type[ICacheManager]) -> None:
        """Register a new cache manager type"""
        cls._managers[cache_type] = manager_class
        logger.info(f"Registered cache manager: {cache_type}")

    @classmethod
    def create_manager(cls, cache_config) -> ICacheManager:
        """Create cache manager based on configuration"""
        # Import here to avoid circular imports
        from .cache_manager import MemoryCacheManager, RedisCacheManager

        # Register default managers if not already registered
        if not cls._managers:
            cls._managers.update({
                'memory': MemoryCacheManager,
                'redis': RedisCacheManager,
            })

        cache_type = getattr(cache_config, 'type', 'memory')

        if cache_type not in cls._managers:
            logger.warning(f"Unknown cache type: {cache_type}, using memory")
            cache_type = 'memory'

        manager_class = cls._managers[cache_type]
        return manager_class(cache_config)

    @classmethod
    def get_available_types(cls) -> List[str]:
        """Get list of available cache types"""
        return list(cls._managers.keys())
