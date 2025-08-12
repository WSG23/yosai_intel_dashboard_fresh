from __future__ import annotations

"""Central plugin service locator consolidating optional utilities."""

import logging
import warnings
from typing import Any, Optional

from ..registry import ServiceRegistry


class _LocatorMeta(type):
    """Intercept deprecated attribute access on the locator."""

    def __getattr__(cls, name: str):
        if name == "get_unicode_handler":
            warnings.warn(
                "PluginServiceLocator.get_unicode_handler() is deprecated; "
                "import from yosai_intel_dashboard.src.core.unicode instead",
                DeprecationWarning,
                stacklevel=2,
            )
            from yosai_intel_dashboard.src.core import (
                unicode as _unicode,  # type: ignore
            )

            return lambda: _unicode
        raise AttributeError(name)


logger = logging.getLogger(__name__)


class PluginServiceLocator(metaclass=_LocatorMeta):
    """Provide access to optional plugin services with lazy loading."""

    # ------------------------------------------------------------------
    @classmethod
    def set_ai_classification_plugin(cls, plugin: Any) -> None:
        ServiceRegistry.register("ai_classification_plugin", plugin)

    @classmethod
    def reset_ai_classification_plugin(cls) -> None:
        ServiceRegistry.remove("ai_classification_plugin")

    # Internal loaders -------------------------------------------------
    @classmethod
    def _load_ai_plugin(cls) -> Optional[Any]:
        try:
            from yosai_intel_dashboard.src.adapters.api.plugins.ai_classification.config import (
                get_ai_config,
            )
            from yosai_intel_dashboard.src.adapters.api.plugins.ai_classification.plugin import (
                AIClassificationPlugin,
            )
        except Exception as exc:  # pragma: no cover - optional
            logger.warning(f"AI classification plugin unavailable: {exc}")
            return None

        plugin = AIClassificationPlugin(get_ai_config())
        if plugin.start():
            return plugin
        logger.warning("AI classification plugin failed to start")
        return None

    @classmethod
    def _load_json_plugin(cls) -> Optional[Any]:
        try:
            from yosai_intel_dashboard.src.core.json_serialization_plugin import (
                quick_start,
            )
        except Exception as exc:  # pragma: no cover - optional
            logger.warning(f"JSON serialization plugin unavailable: {exc}")
            return None

        try:
            return quick_start()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"JSON serialization plugin failed to start: {exc}")
            return None

    # Public API -------------------------------------------------------
    @classmethod
    def get_ai_classification_service(cls) -> Optional[Any]:
        """Return the AI classification plugin instance if available."""
        plugin = ServiceRegistry.get("ai_classification_plugin")
        if plugin is None:
            plugin = cls._load_ai_plugin()
            if plugin is not None:
                ServiceRegistry.register("ai_classification_plugin", plugin)
        return plugin

    @classmethod
    def get_json_serialization_service(cls) -> Optional[Any]:
        """Return the JSON serialization service if available."""
        service = ServiceRegistry.get("json_serialization_service")
        if service is None:
            plugin = cls._load_json_plugin()
            if plugin is not None:
                service = plugin.serialization_service
                ServiceRegistry.register("json_serialization_service", service)
        return service


# Convenience module level functions for backward compatibility ------


def get_ai_classification_service() -> Optional[Any]:
    """Module-level helper used by legacy code and tests."""
    return PluginServiceLocator.get_ai_classification_service()


def set_ai_classification_plugin(plugin: Any) -> None:
    PluginServiceLocator.set_ai_classification_plugin(plugin)


def reset_ai_classification_plugin() -> None:
    PluginServiceLocator.reset_ai_classification_plugin()


def get_json_serialization_service() -> Optional[Any]:
    return PluginServiceLocator.get_json_serialization_service()


__all__ = [
    "PluginServiceLocator",
    "get_ai_classification_service",
    "set_ai_classification_plugin",
    "reset_ai_classification_plugin",
    "get_json_serialization_service",
]


# ---------------------------------------------------------------------------
def __getattr__(name: str):
    if name == "get_unicode_handler":
        warnings.warn(
            "plugins.service_locator.get_unicode_handler() is deprecated; "
            "import from yosai_intel_dashboard.src.core.unicode instead",
            DeprecationWarning,
            stacklevel=2,
        )
        from yosai_intel_dashboard.src.core import unicode as _unicode  # type: ignore

        return lambda: _unicode
    raise AttributeError(name)


# Backwards compatibility for tests that patch _load_ai_plugin
_load_ai_plugin = PluginServiceLocator._load_ai_plugin
