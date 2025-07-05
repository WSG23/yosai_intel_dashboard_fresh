"""Security package exposing validation utilities."""

from core.security import InputValidator
from typing import Protocol


class Validator(Protocol):
    def validate(self, data: str) -> str:
        ...

from .dataframe_validator import DataFrameSecurityValidator
from .sql_validator import SQLInjectionPrevention, SQLSecurityConfig
from .xss_validator import XSSPrevention
from .business_logic_validator import BusinessLogicValidator
from .validation_middleware import ValidationMiddleware, ValidationOrchestrator
from .attack_detection import AttackDetection
from core.exceptions import ValidationError
from .validation_exceptions import SecurityViolation
from .secrets_validator import SecretsValidator, register_health_endpoint

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
    "SecretsValidator",
    "register_health_endpoint",
]
