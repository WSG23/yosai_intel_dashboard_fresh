import logging
from typing import Dict, Any, TYPE_CHECKING

from core.exceptions import ConfigurationError

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from .config import Config

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validate configuration dictionaries."""

    REQUIRED_SECTIONS = {"app", "database", "security"}

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> "Config":
        """Validate config data and return a Config object."""
        if not isinstance(data, dict):
            raise ConfigurationError("Configuration data must be a mapping")

        missing = cls.REQUIRED_SECTIONS - data.keys()
        if missing:
            raise ConfigurationError(
                "Missing configuration sections: " + ", ".join(sorted(missing))
            )

        from .config import Config

        config = Config()
        for section in ["app", "database", "security", "sample_files"]:
            if section in data:
                section_data = data.get(section, {})
                if not isinstance(section_data, dict):
                    raise ConfigurationError(f"Section '{section}' must be a mapping")
                section_obj = getattr(config, section)
                for key, value in section_data.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)
        if "environment" in data:
            config.environment = str(data["environment"])
        if "plugins" in data and isinstance(data["plugins"], dict):
            config.plugins = data["plugins"]
        return config
