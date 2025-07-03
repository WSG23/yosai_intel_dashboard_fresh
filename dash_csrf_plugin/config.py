"""
Configuration classes and enums for CSRF protection plugin
"""

import os
from enum import Enum
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field


class CSRFMode(Enum):
    """CSRF protection modes"""

    AUTO = "auto"  # Automatically detect appropriate mode
    ENABLED = "enabled"  # CSRF protection enabled
    DISABLED = "disabled"  # CSRF protection disabled
    DEVELOPMENT = "development"  # Development mode (CSRF disabled with warnings)
    PRODUCTION = "production"  # Production mode (CSRF enabled with strict settings)
    TESTING = "testing"  # Testing mode (CSRF disabled, testing flags set)


@dataclass
class CSRFConfig:
    """
    Configuration class for CSRF protection

    Provides comprehensive configuration options for CSRF protection
    with sensible defaults for different environments.
    """

    # Core settings
    enabled: bool = True
    secret_key: Optional[str] = None

    # Timing and security
    time_limit: int = 3600  # 1 hour in seconds
    ssl_strict: bool = True
    check_referer: bool = True

    # HTTP methods to protect
    methods: List[str] = field(
        default_factory=lambda: ["POST", "PUT", "PATCH", "DELETE"]
    )

    # Route exemptions
    exempt_routes: List[str] = field(default_factory=list)
    exempt_views: List[str] = field(default_factory=list)

    # Error handling
    custom_error_handler: Optional[Callable] = None
    error_template_path: Optional[str] = None

    # Advanced settings
    field_name: str = "csrf_token"
    header_name: str = "X-CSRFToken"
    hash_algorithm: str = "sha1"

    # Plugin behavior
    auto_exempt_dash_routes: bool = True
    validate_on_callback: bool = True
    include_meta_tag: bool = True

    def __post_init__(self):
        """Post-initialization validation and setup"""
        # Set secret key from environment if not provided
        if not self.secret_key:
            self.secret_key = os.getenv("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY")

        # Validate configuration
        self._validate()

    def _validate(self) -> None:
        """Validate configuration settings"""
        if self.enabled and not self.secret_key:
            raise ValueError("SECRET_KEY is required when CSRF protection is enabled")

        if self.time_limit <= 0:
            raise ValueError("time_limit must be positive")

        if not self.methods:
            raise ValueError("At least one HTTP method must be protected")

    @classmethod
    def for_development(cls, **kwargs) -> "CSRFConfig":
        """Create development configuration"""
        defaults = {
            "enabled": False,
            "ssl_strict": False,
            "check_referer": False,
            "secret_key": "change-me",
        }
        defaults.update(kwargs)
        return cls(**defaults)

    @classmethod
    def for_production(cls, secret_key: str, **kwargs) -> "CSRFConfig":
        """Create production configuration"""
        defaults = {
            "enabled": True,
            "secret_key": secret_key,
            "ssl_strict": True,
            "check_referer": True,
            "time_limit": 3600,
        }
        defaults.update(kwargs)
        return cls(**defaults)

    @classmethod
    def for_testing(cls, **kwargs) -> "CSRFConfig":
        """Create testing configuration"""
        defaults = {
            "enabled": False,
            "ssl_strict": False,
            "check_referer": False,
            "secret_key": "test-secret-key",
        }
        defaults.update(kwargs)
        return cls(**defaults)

    @classmethod
    def from_environment(cls, prefix: str = "CSRF_") -> "CSRFConfig":
        """Create configuration from environment variables"""
        env_config = {}

        # Map environment variables to config attributes
        env_mapping = {
            f"{prefix}ENABLED": (
                "enabled",
                lambda x: x.lower() in ("true", "1", "yes"),
            ),
            f"{prefix}SECRET_KEY": ("secret_key", str),
            f"{prefix}TIME_LIMIT": ("time_limit", int),
            f"{prefix}SSL_STRICT": (
                "ssl_strict",
                lambda x: x.lower() in ("true", "1", "yes"),
            ),
            f"{prefix}CHECK_REFERER": (
                "check_referer",
                lambda x: x.lower() in ("true", "1", "yes"),
            ),
            f"{prefix}METHODS": ("methods", lambda x: x.split(",")),
        }

        for env_var, (attr_name, converter) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    env_config[attr_name] = converter(value)
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid value for {env_var}: {value}") from e

        return cls(**env_config)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "CSRFConfig":
        """Create configuration from dictionary"""
        # Filter out unknown keys
        valid_keys = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_config = {k: v for k, v in config_dict.items() if k in valid_keys}
        return cls(**filtered_config)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "enabled": self.enabled,
            "secret_key": "***" if self.secret_key else None,  # Mask secret key
            "time_limit": self.time_limit,
            "ssl_strict": self.ssl_strict,
            "check_referer": self.check_referer,
            "methods": self.methods,
            "exempt_routes": self.exempt_routes,
            "exempt_views": self.exempt_views,
            "field_name": self.field_name,
            "header_name": self.header_name,
            "hash_algorithm": self.hash_algorithm,
            "auto_exempt_dash_routes": self.auto_exempt_dash_routes,
            "validate_on_callback": self.validate_on_callback,
            "include_meta_tag": self.include_meta_tag,
        }

    def update(self, **kwargs) -> "CSRFConfig":
        """Create new configuration with updated values"""
        current_dict = self.to_dict()
        current_dict.update(kwargs)
        return self.from_dict(current_dict)

    def add_exempt_route(self, route: str) -> None:
        """Add route to exemption list"""
        if route not in self.exempt_routes:
            self.exempt_routes.append(route)

    def add_exempt_view(self, view: str) -> None:
        """Add view to exemption list"""
        if view not in self.exempt_views:
            self.exempt_views.append(view)

    def remove_exempt_route(self, route: str) -> None:
        """Remove route from exemption list"""
        if route in self.exempt_routes:
            self.exempt_routes.remove(route)

    def remove_exempt_view(self, view: str) -> None:
        """Remove view from exemption list"""
        if view in self.exempt_views:
            self.exempt_views.remove(view)


# Factory functions for common configurations


def create_development_config(**kwargs) -> CSRFConfig:
    """Create development configuration with CSRF disabled"""
    return CSRFConfig.for_development(**kwargs)


def create_production_config(secret_key: str, **kwargs) -> CSRFConfig:
    """Create production configuration with CSRF enabled"""
    return CSRFConfig.for_production(secret_key, **kwargs)


def create_testing_config(**kwargs) -> CSRFConfig:
    """Create testing configuration"""
    return CSRFConfig.for_testing(**kwargs)


def auto_detect_config(app: dash.Dash, **kwargs) -> CSRFConfig:
    """Auto-detect appropriate configuration based on app settings"""
    app_type = CSRFUtils.detect_dash_app_type(app)

    if app_type == "development":
        return create_development_config(**kwargs)
    elif app_type == "testing":
        return create_testing_config(**kwargs)
    else:
        secret_key = kwargs.get("secret_key") or app.server.config.get("SECRET_KEY")
        if not secret_key:
            raise ValueError("SECRET_KEY required for production configuration")
        return create_production_config(secret_key, **kwargs)
