from __future__ import annotations

"""Central plugin service locator consolidating optional utilities."""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PluginServiceLocator:
    """Provide access to optional plugin services with lazy loading."""

    _ai_plugin: Optional[Any] = None
    _json_plugin: Optional[Any] = None

    # ------------------------------------------------------------------
    @classmethod
    def set_ai_classification_plugin(cls, plugin: Any) -> None:
        cls._ai_plugin = plugin

    @classmethod
    def reset_ai_classification_plugin(cls) -> None:
        cls._ai_plugin = None

    # Internal loaders -------------------------------------------------
    @classmethod
    def _load_ai_plugin(cls) -> Optional[Any]:
        try:
            from plugins.ai_classification.plugin import AIClassificationPlugin
            from plugins.ai_classification.config import get_ai_config
        except Exception as exc:  # pragma: no cover - optional
            logger.warning("AI classification plugin unavailable: %s", exc)
            return None

        plugin = AIClassificationPlugin(get_ai_config())
        if plugin.start():
            return plugin
        logger.warning("AI classification plugin failed to start")
        return None

    @classmethod
    def _load_json_plugin(cls) -> Optional[Any]:
        try:
            from core.json_serialization_plugin import quick_start
        except Exception as exc:  # pragma: no cover - optional
            logger.warning("JSON serialization plugin unavailable: %s", exc)
            return None

        try:
            return quick_start()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("JSON serialization plugin failed to start: %s", exc)
            return None

    # Public API -------------------------------------------------------
    @classmethod
    def get_ai_classification_service(cls) -> Optional[Any]:
        """Return the AI classification plugin instance if available."""
        if cls._ai_plugin is None:
            cls._ai_plugin = cls._load_ai_plugin()
        return cls._ai_plugin

    @classmethod
    def get_json_serialization_service(cls) -> Optional[Any]:
        """Return the JSON serialization service if available."""
        if cls._json_plugin is None:
            cls._json_plugin = cls._load_json_plugin()
        if cls._json_plugin is not None:
            return cls._json_plugin.serialization_service
        return None

    @staticmethod
    def get_unicode_handler():
        """Return the unified Unicode handler module."""
        from utils import unicode_utils

        return unicode_utils


# Convenience module level functions for backward compatibility ------

_ai_plugin: Optional[Any] = None


def get_ai_classification_service() -> Optional[Any]:
    """Module-level helper used by legacy code and tests."""
    global _ai_plugin
    if _ai_plugin is None:
        _ai_plugin = _load_ai_plugin()
    return _ai_plugin


def set_ai_classification_plugin(plugin: Any) -> None:
    global _ai_plugin
    _ai_plugin = plugin


def reset_ai_classification_plugin() -> None:
    global _ai_plugin
    _ai_plugin = None


def get_json_serialization_service() -> Optional[Any]:
    return PluginServiceLocator.get_json_serialization_service()


def get_unicode_handler():
    return PluginServiceLocator.get_unicode_handler()


__all__ = [
    "PluginServiceLocator",
    "get_ai_classification_service",
    "set_ai_classification_plugin",
    "reset_ai_classification_plugin",
    "get_json_serialization_service",
    "get_unicode_handler",
]

# Backwards compatibility for tests that patch _load_ai_plugin
_load_ai_plugin = PluginServiceLocator._load_ai_plugin
