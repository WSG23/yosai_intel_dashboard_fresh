import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List

from core.exceptions import ConfigurationError

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from .config import Config

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validate configuration dictionaries."""

    REQUIRED_SECTIONS = {"app", "database", "security"}
    DEFAULT_RULES: Dict[str, Dict[str, Any]] = {}

    @dataclass
    class ValidationResult:
        """Container for a single validation message."""

        message: str
        severity: str = "info"

    @classmethod
    def _setup_default_rules(cls) -> None:
        """Initialize built in validation rules."""
        if cls.DEFAULT_RULES:
            return

        cls.DEFAULT_RULES = {
            "database.type": {
                "allowed": ["sqlite", "postgresql", "mock"],
                "severity": "error",
            },
            "app.secret_key": {"required": True, "severity": "warning"},
            "security.secret_key": {"required": True, "severity": "warning"},
        }

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
    def validate_structure(
        cls, config: "Config"
    ) -> List["ConfigValidator.ValidationResult"]:
        """Check that required sections exist."""
        results: List[ConfigValidator.ValidationResult] = []
        for section in cls.REQUIRED_SECTIONS:
            if not hasattr(config, section):
                results.append(
                    cls.ValidationResult(
                        f"Missing configuration section: {section}", "error"
                    )
                )
        return results

    @classmethod
    def validate_values(
        cls, config: "Config"
    ) -> List["ConfigValidator.ValidationResult"]:
        """Validate configuration option values."""
        cls._setup_default_rules()
        results: List[ConfigValidator.ValidationResult] = []

        rules = cls.DEFAULT_RULES

        # database.type allowed values
        rule = rules.get("database.type")
        if rule and config.database.type not in rule.get("allowed", []):
            results.append(
                cls.ValidationResult(
                    f"Invalid database type: {config.database.type}",
                    rule.get("severity", "error"),
                )
            )

        # required secret keys
        for path in ["app.secret_key", "security.secret_key"]:
            rule = rules.get(path)
            if rule and rule.get("required"):
                section, attr = path.split(".")
                value = getattr(getattr(config, section), attr, "")
                if not value:
                    results.append(
                        cls.ValidationResult(
                            f"{path} is required", rule.get("severity", "warning")
                        )
                    )

        # simple numeric checks
        if config.app.port <= 0:
            results.append(cls.ValidationResult("app.port must be positive", "error"))
        if config.database.port <= 0:
            results.append(
                cls.ValidationResult("database.port must be positive", "error")
            )

        return results

    @classmethod
    def validate_environment_specific(
        cls, config: "Config"
    ) -> List["ConfigValidator.ValidationResult"]:
        """Checks that depend on the current environment."""
        results: List[ConfigValidator.ValidationResult] = []
        env = getattr(config, "environment", "development")

        if env == "production":
            if config.app.secret_key in {
                "dev-key-change-in-production",
                "change-me",
                "",
            }:
                results.append(
                    cls.ValidationResult(
                        "SECRET_KEY must be set for production", "error"
                    )
                )
            if not config.database.password and config.database.type != "sqlite":
                results.append(
                    cls.ValidationResult(
                        "Production database requires password", "warning"
                    )
                )
            if config.app.host == "127.0.0.1":
                results.append(
                    cls.ValidationResult(
                        "Production should not run on localhost", "warning"
                    )
                )

        if config.app.debug and config.app.host == "0.0.0.0":
            results.append(
                cls.ValidationResult(
                    "Debug mode with host 0.0.0.0 is a security risk", "warning"
                )
            )
        if config.database.type == "postgresql" and not config.database.password:
            results.append(
                cls.ValidationResult("PostgreSQL requires a password", "warning")
            )

        return results
