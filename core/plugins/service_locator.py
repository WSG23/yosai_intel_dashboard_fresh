"""Simple plugin service locator used by components."""

from __future__ import annotations

import logging
from typing import Any, Optional

_ai_plugin: Optional[Any] = None
logger = logging.getLogger(__name__)


def set_ai_classification_plugin(plugin: Any) -> None:
    """Set the global AI classification plugin (primarily for tests)."""
    global _ai_plugin
    _ai_plugin = plugin


def reset_ai_classification_plugin() -> None:
    """Reset the cached AI classification plugin."""
    global _ai_plugin
    _ai_plugin = None


def _load_ai_plugin() -> Optional[Any]:
    try:
        from plugins.ai_classification.plugin import AIClassificationPlugin
        from plugins.ai_classification.config import get_ai_config
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.warning("AI classification plugin unavailable: %s", exc)
        return None

    plugin = AIClassificationPlugin(get_ai_config())
    if plugin.start():
        return plugin
    logger.warning("AI classification plugin failed to start")
    return None


def get_ai_classification_service() -> Optional[Any]:
    """Return the cached :class:`AIClassificationPlugin` instance if available."""
    global _ai_plugin
    if _ai_plugin is None:
        _ai_plugin = _load_ai_plugin()
    return _ai_plugin


__all__ = [
    "get_ai_classification_service",
    "set_ai_classification_plugin",
    "reset_ai_classification_plugin",
]
