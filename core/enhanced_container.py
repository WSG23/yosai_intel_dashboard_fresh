from typing import Dict, Any, TypeVar, Type, Callable, Optional
import logging

T = TypeVar('T')
logger = logging.getLogger(__name__)

class ServiceContainer:
    """Enterprise dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton service instance."""
        self._singletons[name] = instance
        logger.debug(f"Registered singleton service: {name}")
    
    def register_factory(self, name: str, factory: Callable[[], T]) -> None:
        """Register a factory function for service creation."""
        self._factories[name] = factory
        logger.debug(f"Registered factory for service: {name}")
    
    def get(self, name: str) -> Any:
        """Get a service by name."""
        # Check singletons first
        if name in self._singletons:
            return self._singletons[name]
        
        # Check if factory exists
        if name in self._factories:
            instance = self._factories[name]()
            self._singletons[name] = instance  # Cache as singleton
            return instance
        
        raise ValueError(f"Service '{name}' not found")
    
    def has(self, name: str) -> bool:
        """Check if service is registered."""
        return name in self._singletons or name in self._factories
