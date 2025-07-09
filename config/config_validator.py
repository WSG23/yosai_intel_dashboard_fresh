import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Dict, List

from core.exceptions import ConfigurationError

from .protocols import ConfigValidatorProtocol

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from .base import Config

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Outcome of configuration validation."""

    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ConfigValidator(ConfigValidatorProtocol):
    """Validate configuration dictionaries."""

    REQUIRED_SECTIONS = {"app", "database", "security"}
    _custom_rules: List[Callable[["Config", ValidationResult], None]] = []

    @classmethod
    def register_rule(cls, func: Callable[["Config", ValidationResult], None]) -> None:
        """Register a custom validation rule."""
        cls._custom_rules.append(func)

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

        from .base import Config

        config = Config()
        for section in [
            "app",
            "database",
            "security",
            "sample_files",
            "analytics",
            "monitoring",
            "cache",
            "secret_validation",
        ]:
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
        return config

    # ------------------------------------------------------------------
    @classmethod
    def run_checks(cls, config: "Config") -> ValidationResult:
        """Run built-in and custom validation rules."""
        result = ValidationResult()

        if config.environment == "production":
            if config.app.secret_key in {
                "dev-key-change-in-production",
                "change-me",
                "",
            }:
                result.errors.append("SECRET_KEY must be set for production")
            if not config.database.password and config.database.type != "sqlite":
                result.warnings.append("Production database requires password")
            if config.app.host == "127.0.0.1":
                result.warnings.append("Production should not run on localhost")

        for rule in cls._custom_rules:
            try:
                rule(config, result)
            except Exception as exc:  # pragma: no cover - defensive
                result.warnings.append(f"Custom rule error: {exc}")

        result.valid = not result.errors
        return result


__all__ = ["ConfigValidator", "ValidationResult"]
