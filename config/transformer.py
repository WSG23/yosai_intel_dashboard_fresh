from __future__ import annotations

import logging
from typing import Callable, Dict, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .config import ConfigManager

logger = logging.getLogger(__name__)


class ConfigTransformer:
    """Registry for configuration transformation callbacks."""

    def __init__(self) -> None:
        self._callbacks: Dict[str, Callable[[ConfigManager], None]] = {}

    def register(self, section: str, func: Callable[[ConfigManager], None]) -> None:
        """Register a callback to transform a configuration section."""
        self._callbacks[section] = func

    def apply(self, manager: ConfigManager) -> None:
        """Apply all registered callbacks to ``manager``."""
        for name, func in self._callbacks.items():
            try:
                func(manager)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed applying %s overrides: %s", name, exc)


# Shared instance used by ConfigManager
config_transformer = ConfigTransformer()
