"""
Self-Contained JSON Serialization Plugin
Handles all JSON serialization issues internally with minimal external dependencies
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from typing import Any, Dict, Optional, cast

import pandas as pd

from yosai_intel_dashboard.src.core.protocols.plugin import PluginMetadata
from yosai_intel_dashboard.src.core.serialization import SafeJSONSerializer

from .base_model import BaseModel

# Optional Babel support is handled at runtime

logger = logging.getLogger(__name__)


@dataclass
class JsonSerializationConfig:
    """Configuration for JSON serialization plugin"""

    enabled: bool = True
    max_dataframe_rows: int = 99
    max_string_length: int = 10000
    include_type_metadata: bool = True
    compress_large_objects: bool = True
    fallback_to_repr: bool = True
    auto_wrap_callbacks: bool = True


class YosaiJSONEncoder(json.JSONEncoder):
    """Self-contained JSON encoder that handles all problematic types.

    DataFrame previews always use ``df.head(5)`` and are clamped to fewer than
    100 rows. If the serialized preview exceeds 5MB, the ``data`` field is
    replaced with an empty list and ``truncated`` flag.
    """

    def __init__(
        self, config: Optional[JsonSerializationConfig] = None, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.config = config or JsonSerializationConfig()

    def default(self, o: Any) -> Any:
        """Handle all problematic types for JSON serialization"""

        # Handle LazyString objects
        if self._is_lazystring(o):
            return str(o)

        # Handle pandas DataFrames
        if isinstance(o, pd.DataFrame):
            max_rows = min(self.config.max_dataframe_rows, 99)
            preview_df = o.head(max_rows)
            preview_records = preview_df.head(5).to_dict("records")
            payload = {
                "__type__": "DataFrame",
                "data": preview_records,
                "shape": o.shape,
                "columns": list(o.columns),
            }
            serialized = json.dumps(payload)
            if len(serialized.encode("utf-8")) >= 5 * 1024 * 1024:
                payload["data"] = []
                payload["truncated"] = True
            return payload

        # Handle pandas Series
        if isinstance(o, pd.Series):
            return {
                "__type__": "Series",
                "data": o.head(self.config.max_dataframe_rows).tolist(),
                "name": o.name,
            }

        # Handle datetime objects
        if isinstance(o, (datetime, date)):
            return o.isoformat()

        # Handle numpy types
        if hasattr(o, "dtype") and hasattr(o, "tolist"):
            try:
                return o.tolist()
            except Exception:
                return str(o)

        # Handle dataclasses
        if is_dataclass(o):
            try:
                return asdict(o)
            except Exception:
                return str(o)

        # Handle callable objects
        if callable(o):
            return f"<function {getattr(o, '__name__', 'anonymous')}>"

        # Handle complex objects with __dict__
        if hasattr(o, "__dict__"):
            try:
                return {
                    "__type__": o.__class__.__name__,
                    "__module__": getattr(o.__class__, "__module__", None),
                    "__dict__": {
                        k: self._safe_serialize(v) for k, v in o.__dict__.items()
                    },
                }
            except Exception:
                return str(o)

        # Fallback to string representation
        return str(o)

    def _is_lazystring(self, obj: Any) -> bool:
        """Check if object is a LazyString"""
        try:
            from flask_babel import LazyString as BabelLazyString  # type: ignore

            if isinstance(obj, BabelLazyString):
                return True
        except Exception:
            pass
        # Additional check for LazyString-like objects
        return hasattr(obj, "__class__") and "LazyString" in str(obj.__class__)

    def _safe_serialize(self, obj: Any) -> Any:
        """Safely serialize any object"""
        try:
            # Test if object is already JSON serializable
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return self.default(obj)


class JsonSerializationService:
    """Self-contained JSON serialization service"""

    def __init__(self, config: Optional[JsonSerializationConfig] = None):
        self.config = config or JsonSerializationConfig()
        self.encoder = YosaiJSONEncoder(self.config)
        self._sanitizer = SafeJSONSerializer()

    def serialize(self, obj: Any) -> str:
        """Serialize object to JSON string"""
        sanitized = self._sanitizer.serialize(obj)
        try:
            return json.dumps(
                sanitized, cls=YosaiJSONEncoder, config=self.config, ensure_ascii=False
            )
        except Exception as e:
            logger.warning(f"Serialization failed, using fallback: {e}")
            return json.dumps({"error": "Serialization failed", "repr": str(sanitized)})

    def sanitize_for_transport(self, obj: Any) -> Any:
        """Sanitize object for JSON transport"""
        sanitized = self._sanitizer.serialize(obj)
        return self.encoder._safe_serialize(sanitized)


class JsonCallbackService:
    """Wrap callbacks and sanitize their outputs using ``JsonSerializationService``."""

    def __init__(self, serialization_service: JsonSerializationService):
        self._service = serialization_service

    def handle_wrap(self, func):
        """Return a wrapper that sanitizes the callback result and catches errors."""

        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except Exception as exc:  # pragma: no cover - simple error wrapper
                return {"error": True, "message": str(exc)}
            return self._service.sanitize_for_transport(result)

        return wrapper


class JsonSerializationPlugin(BaseModel):
    """Self-contained JSON Serialization Plugin"""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self.config: Optional[JsonSerializationConfig] = None
        self.serialization_service: Optional[JsonSerializationService] = None
        self.callback_service: Optional[JsonCallbackService] = None
        self._started = False
        self._original_dumps = None
        self._babel_available = False

    metadata = PluginMetadata(
        name="json_serialization",
        version="1.0.0",
        description="Self-contained JSON serialization utilities",
        author="Yōsai",
    )

    def _handle_babel_safely(self):
        """Handle babel imports and LazyString conversion within the plugin"""
        try:
            self._babel_available = True

            # Patch any babel lazy_gettext to return strings immediately
            try:
                import flask_babel

                if hasattr(flask_babel, "lazy_gettext"):
                    original_lazy_gettext = flask_babel.lazy_gettext

                    def safe_lazy_gettext(text):
                        result = original_lazy_gettext(text)
                        return str(result)  # Convert to string immediately

                    flask_babel.lazy_gettext = safe_lazy_gettext
                    self.logger.info(
                        "✅ Patched flask_babel.lazy_gettext to return strings"
                    )
            except Exception as e:
                self.logger.warning(f"Could not patch flask_babel: {e}")

        except ImportError:
            self._babel_available = False
            self.logger.info("Flask-Babel not available, using safe fallbacks")

    def load(self, container: Any = None, config: Dict[str, Any] = None) -> bool:
        """Load the plugin with optional container and config"""
        try:
            self.logger.info("Loading JSON Serialization Plugin...")

            # Create configuration
            config = config or {}
            self.config = JsonSerializationConfig(**config)

            # Create services
            self.serialization_service = JsonSerializationService(self.config)
            self.callback_service = JsonCallbackService(self.serialization_service)

            # Register with container if provided
            if container and hasattr(container, "register"):
                try:
                    container.register(
                        "json_serialization_service", self.serialization_service
                    )
                    container.register(
                        "serialization_service", self.serialization_service
                    )
                    container.register("json_callback_service", self.callback_service)
                except Exception as e:
                    self.logger.warning(f"Could not register with container: {e}")

            self.logger.info("JSON Serialization Plugin loaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load JSON Serialization Plugin: {e}")
            return False

    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure the plugin"""
        try:
            if config and self.config:
                for key, value in config.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)

            self.logger.info("JSON Serialization Plugin configured")
            return True

        except Exception as e:
            self.logger.error(f"Failed to configure JSON Serialization Plugin: {e}")
            return False

    def start(self) -> bool:
        """Start the plugin and apply global JSON patches"""
        try:
            if self._started:
                return True

            # Handle babel safely
            self._handle_babel_safely()

            # Apply global JSON patch
            self._apply_global_json_patch()

            self._started = True
            self.logger.info("✅ JSON Serialization Plugin started with babel handling")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start JSON Serialization Plugin: {e}")
            return False

    def _apply_global_json_patch(self):
        """Apply global JSON.dumps patch"""
        if not hasattr(json, "_yosai_original_dumps"):
            # Store original dumps
            json._yosai_original_dumps = json.dumps

            # Create patched dumps function
            def safe_dumps(obj, **kwargs):
                try:
                    # Use our encoder
                    if "cls" not in kwargs:
                        kwargs["cls"] = YosaiJSONEncoder
                        kwargs["config"] = self.config
                    return json._yosai_original_dumps(obj, **kwargs)
                except Exception:
                    # Ultimate fallback
                    return json._yosai_original_dumps(
                        {"error": "Serialization failed", "repr": str(obj)}
                    )

            # Apply patch
            json.dumps = safe_dumps
            self.logger.info("Applied global JSON.dumps patch")

            self._started = True
            self.logger.info("✅ JSON Serialization Plugin started with babel handling")
            return True

    def stop(self) -> bool:
        """Stop the plugin and restore original JSON functions"""
        try:
            # Restore original JSON.dumps if we patched it
            if hasattr(json, "_yosai_original_dumps"):
                json.dumps = json._yosai_original_dumps
                delattr(json, "_yosai_original_dumps")

            self._started = False
            self.logger.info("JSON Serialization Plugin stopped")
            return True

        except Exception as e:
            self.logger.error(f"Failed to stop JSON Serialization Plugin: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Return plugin health status"""
        try:
            # Test basic serialization
            test_data = {"test": "data", "number": 42}
            serialized = self.serialization_service.serialize(test_data)

            return {
                "healthy": True,
                "started": self._started,
                "service_available": self.serialization_service is not None,
                "test_passed": serialized is not None,
                "babel_available": self._babel_available,
            }

        except Exception as e:
            return {"healthy": False, "error": str(e), "started": self._started}


# Simple container for when none is provided
class SimpleContainer(BaseModel):
    """Minimal container implementation"""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self._services = {}

    def register(self, name: str, service: Any):
        self._services[name] = service

    def get(self, name: str):
        return self._services.get(name)

    def has(self, name: str):
        return name in self._services


# Factory functions
def create_plugin() -> JsonSerializationPlugin:
    """Factory function for plugin discovery"""
    return JsonSerializationPlugin()


def quick_start() -> JsonSerializationPlugin:
    """Quick start the plugin with default settings"""
    plugin = JsonSerializationPlugin()
    container = SimpleContainer()

    plugin.load(
        container,
        {"enabled": True, "max_dataframe_rows": 1000, "auto_wrap_callbacks": True},
    )
    plugin.configure({})
    plugin.start()

    return plugin


# Auto-start removed to avoid side effects on import.
# Use ``quick_start`` explicitly if needed.
