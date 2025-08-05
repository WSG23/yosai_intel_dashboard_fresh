"""Configuration interfaces for better modularity"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from yosai_intel_dashboard.src.database.types import DBRows


@dataclass
class ConnectionResult:
    """Standard connection result"""

    success: bool
    connection: Any
    error_message: Optional[str] = None
    connection_type: Optional[str] = None


class IDatabaseManager(ABC):
    """Database manager interface for dependency injection"""

    @abstractmethod
    def get_connection(self) -> ConnectionResult:
        """Get database connection"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if connection is working"""
        pass

    @abstractmethod
    def close_connection(self) -> None:
        """Close database connection"""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict] = None) -> DBRows:
        """Execute database query"""
        pass


class ICacheManager(ABC):
    """Cache manager interface for dependency injection"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries"""
        pass

    @abstractmethod
    def start(self) -> None:
        """Initialize cache"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop cache"""
        pass


class IConfigurationManager(ABC):
    """Configuration manager interface"""

    @abstractmethod
    def load_configuration(self, config_path: Optional[str] = None) -> None:
        """Load configuration from file or defaults"""
        pass

    @abstractmethod
    def get_database_config(self) -> Any:
        """Get database configuration"""
        pass

    @abstractmethod
    def get_cache_config(self) -> Any:
        """Get cache configuration"""
        pass

    @abstractmethod
    def get_app_config(self) -> Any:
        """Get app configuration"""
        pass
