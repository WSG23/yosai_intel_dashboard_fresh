"""Security package exposing current validation utilities.

This package provides unified security validation through SecurityValidator.
All deprecated individual validators have been removed and consolidated.
"""

from core.exceptions import ValidationError

from .attack_detection import AttackDetection
from .secrets_validator import SecretsValidator, register_health_endpoint
from .secure_query_wrapper import (
    execute_secure_command,
    execute_secure_sql,
)
from .unicode_security_validator import UnicodeSecurityValidator
from .validation_exceptions import SecurityViolation


def __getattr__(name: str):
    """Lazily provide heavy validators to avoid circular imports."""

    if name == "SecurityValidator":
        from validation.security_validator import SecurityValidator as _SV

        return _SV
    if name == "UnicodeValidator":
        from validation.unicode_validator import UnicodeValidator as _UV

        return _UV
    if name in {"UnicodeSurrogateValidator", "SurrogateHandlingConfig"}:
        from .unicode_surrogate_validator import SurrogateHandlingConfig as _SHC
        from .unicode_surrogate_validator import UnicodeSurrogateValidator as _USV

        return {
            "UnicodeSurrogateValidator": _USV,
            "SurrogateHandlingConfig": _SHC,
        }[name]
    raise AttributeError(name)


# Public API - Only current, non-deprecated classes
__all__ = [
    # Core validation
    "SecurityValidator",
    "ValidationError",
    "SecurityViolation",
    # Specialized validators
    "UnicodeSecurityValidator",
    "UnicodeValidator",
    "UnicodeSurrogateValidator",
    "SurrogateHandlingConfig",
    # Security utilities
    "AttackDetection",
    "SecretsValidator",
    "register_health_endpoint",
    "execute_secure_sql",
    "execute_secure_command",
]
