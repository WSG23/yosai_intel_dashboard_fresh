"""Security package exposing current validation utilities.

This package provides unified security validation through SecurityValidator.
All deprecated individual validators have been removed and consolidated.
"""

from core.exceptions import ValidationError
from .attack_detection import AttackDetection
from .secrets_validator import SecretsValidator, register_health_endpoint
from .unicode_security_validator import UnicodeSecurityValidator
from .unicode_surrogate_validator import (
    SurrogateHandlingConfig,
    UnicodeSurrogateValidator,
)
from .validation_exceptions import SecurityViolation


def __getattr__(name: str):
    """Lazily provide ``SecurityValidator`` to avoid circular imports."""

    if name == "SecurityValidator":
        from core.security_validator import SecurityValidator as _SV

        return _SV
    raise AttributeError(name)

# Public API - Only current, non-deprecated classes
__all__ = [
    # Core validation
    "SecurityValidator",
    "ValidationError",
    "SecurityViolation",

    # Specialized validators
    "UnicodeSecurityValidator",
    "UnicodeSurrogateValidator",
    "SurrogateHandlingConfig",

    # Security utilities
    "AttackDetection",
    "SecretsValidator",
    "register_health_endpoint",
]
