"""LazyString sanitization and Flask integration plugin."""

from __future__ import annotations

import logging
import unicodedata
from dataclasses import dataclass
from typing import Any

from core.protocols.plugin import PluginMetadata
from core.serialization import SafeJSONSerializer
from core.unicode import sanitize_unicode_input

# Optional Babel import
try:
    from flask_babel import LazyString

    BABEL_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    LazyString = None  # type: ignore
    BABEL_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class LazyStringFixConfig:
    """Configuration options for ``LazyString`` sanitization."""

    enabled: bool = True
    auto_wrap_callbacks: bool = True
    deep_sanitize: bool = True
    log_conversions: bool = False
    fallback_locale: str = "en"


class LazyStringFixPlugin:
    """Minimal plugin object returned by :func:`initialize_lazystring_fix`."""

    metadata = PluginMetadata(
        name="lazystring_fix",
        version="1.0.0",
        description="Sanitize LazyString objects and patch JSON handling",
        author="Yōsai",
    )

    def __init__(self, config: LazyStringFixConfig) -> None:
        self.config = config
        self.conversion_count = 0

    def get_stats(self) -> dict[str, Any]:
        return {"conversions": self.conversion_count}


# Global plugin instance used by sanitize_lazystring
_plugin: LazyStringFixPlugin | None = None
_serializer = SafeJSONSerializer()


def _is_lazy_string(obj: Any) -> bool:
    if BABEL_AVAILABLE and isinstance(obj, LazyString):
        return True
    return hasattr(obj, "__class__") and "LazyString" in str(obj.__class__)


def _sanitize_text(text: str) -> str:
    """Return sanitized text using :func:`sanitize_unicode_input`."""
    return sanitize_unicode_input(text)


def sanitize_lazystring(obj: Any) -> Any:
    """Recursively sanitize LazyString objects inside ``obj``."""
    global _plugin
    config = _plugin.config if _plugin else LazyStringFixConfig()

    try:
        if _is_lazy_string(obj) and _plugin:
            _plugin.conversion_count += 1
            if config.log_conversions:
                logger.debug("Converted LazyString %r", obj)
        return _serializer.serialize(obj)
    except Exception as exc:  # pragma: no cover - defensive
        if config.log_conversions:
            logger.error("LazyString sanitization failed: %s", exc)

    return obj


def initialize_lazystring_fix(app, config: LazyStringFixConfig) -> LazyStringFixPlugin:
    """Patch Flask JSON handling to sanitize ``LazyString`` objects."""

    global _plugin
    _plugin = LazyStringFixPlugin(config)

    class SanitizingJSONProvider(app.json_provider_class):
        def dumps(self, obj, **kwargs):
            obj = _serializer.serialize(obj)
            return super().dumps(obj, **kwargs)

    app.json_provider_class = SanitizingJSONProvider
    app.json = SanitizingJSONProvider(app)
    app.extensions["lazystring_fix"] = _plugin
    return _plugin
