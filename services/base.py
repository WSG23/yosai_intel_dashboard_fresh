"""
Base service classes and interfaces for Yōsai Intel Dashboard
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol
import logging

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Base class for all services"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize the service"""
        try:
            self._do_initialize()
            self._initialized = True
            self.logger.info(f"Service {self.name} initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize service {self.name}: {e}")
            return False

    @abstractmethod
    def _do_initialize(self) -> None:
        """Implement service-specific initialization"""
        pass

    def is_initialized(self) -> bool:
        """Check if service is initialized"""
        return self._initialized

    def health_check(self) -> Dict[str, Any]:
        """Basic health check"""
        return {
            "name": self.name,
            "status": "healthy" if self._initialized else "unhealthy",
            "initialized": self._initialized,
        }


class MockService(BaseService):
    """Mock service for testing"""

    def __init__(self, name: str = "mock_service"):
        super().__init__(name)

    def _do_initialize(self) -> None:
        """Mock initialization"""
        pass

    def get_data(self) -> Dict[str, Any]:
        """Return mock data"""
        return {"status": "mock", "service": self.name}
