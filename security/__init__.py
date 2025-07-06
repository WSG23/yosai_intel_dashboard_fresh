"""Security package exposing validation utilities."""

from typing import Protocol

from core.security import InputValidator


class Validator(Protocol):
    def validate(self, data: str) -> str:
        ...

from core.exceptions import ValidationError

from .attack_detection import AttackDetection
from .business_logic_validator import BusinessLogicValidator
from .dataframe_validator import DataFrameSecurityValidator
from .secrets_validator import SecretsValidator, register_health_endpoint
from .sql_validator import SQLInjectionPrevention, SQLSecurityConfig
from .unicode_security_validator import UnicodeSecurityValidator
from .unicode_surrogate_validator import (
    SurrogateHandlingConfig,
    UnicodeSurrogateValidator,
)
from .validation_exceptions import SecurityViolation

__all__ = [
    "InputValidator",
    "Validator",
    "DataFrameSecurityValidator",
    "SQLSecurityConfig",
    "SQLInjectionPrevention",
    "XSSPrevention",
    "BusinessLogicValidator",
    "ValidationMiddleware",
    "ValidationOrchestrator",
    "AttackDetection",
    "ValidationError",
    "SecurityViolation",
    "UnicodeSecurityValidator",
    "SecretsValidator",
    "register_health_endpoint",
    "UnicodeSurrogateValidator",
    "SurrogateHandlingConfig",
]
