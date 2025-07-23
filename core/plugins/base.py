#!/usr/bin/env python3
"""
Base Plugin Class for Yōsai Intel Dashboard Plugin System
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from core.base_model import BaseModel

from .protocols import PluginMetadata, PluginProtocol, PluginStatus

logger = logging.getLogger(__name__)


class BasePlugin(BaseModel, ABC, PluginProtocol):
    """
    Abstract base class for all plugins in the Yōsai Intel Dashboard

    Provides common functionality and enforces the plugin interface
    """

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self.name: str = ""
        self.version: str = "1.0.0"
        self.description: str = ""
        self.author: str = ""
        self.dependencies: list = []
        self.status: PluginStatus = PluginStatus.DISCOVERED
        self._container: Optional[Any] = None
        self._config: Optional[Dict[str, Any]] = None

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name=self.name,
            version=self.version,
            description=self.description,
            author=self.author,
            dependencies=self.dependencies,
        )

    def load(self, container: Any, config: Dict[str, Any]) -> bool:
        """Load the plugin with container and configuration"""
        try:
            self._container = container
            self._config = config
            self.status = PluginStatus.LOADED
            logger.debug(f"Plugin {self.name} loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load plugin {self.name}: {e}")
            self.status = PluginStatus.FAILED
            return False

    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure the plugin with provided settings"""
        try:
            self._config = config
            self.status = PluginStatus.CONFIGURED
            logger.debug(f"Plugin {self.name} configured successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to configure plugin {self.name}: {e}")
            self.status = PluginStatus.FAILED
            return False

    def start(self) -> bool:
        """Start the plugin - perform any runtime initialization"""
        try:
            self.status = PluginStatus.STARTED
            logger.debug(f"Plugin {self.name} started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start plugin {self.name}: {e}")
            self.status = PluginStatus.FAILED
            return False

    def stop(self) -> bool:
        """Stop the plugin - perform cleanup"""
        try:
            self.status = PluginStatus.STOPPED
            logger.debug(f"Plugin {self.name} stopped successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to stop plugin {self.name}: {e}")
            self.status = PluginStatus.FAILED
            return False

    def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status"""
        return {
            "healthy": self.status == PluginStatus.STARTED,
            "status": (
                self.status.value if hasattr(self.status, "value") else str(self.status)
            ),
            "name": self.name,
            "version": self.version,
        }

    @abstractmethod
    def initialize(self, container: Any, config: Dict[str, Any]) -> bool:
        """Initialize the plugin - implement plugin-specific initialization logic"""
        pass

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        if not self._config:
            return default
        return self._config.get(key, default)

    def get_container(self) -> Optional[Any]:
        """Get the dependency injection container"""
        return self._container

    def __str__(self) -> str:
        """String representation of the plugin"""
        return f"{self.name} v{self.version} ({self.status})"

    def __repr__(self) -> str:
        """Detailed string representation"""
        return (
            f"<{self.__class__.__name__}(name='{self.name}', "
            f"version='{self.version}', status='{self.status}')>"
        )
