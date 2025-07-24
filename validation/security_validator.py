from __future__ import annotations

import html
import re
from typing import Iterable

from config.dynamic_config import dynamic_config
from core.exceptions import ValidationError

from .core import ValidationResult
from .file_validator import FileValidator
from .rules import CompositeValidator, ValidationRule


class XSSRule(ValidationRule):
    PATTERN = re.compile(r"(<script|onerror=|javascript:)", re.IGNORECASE)

    def validate(self, data: str) -> ValidationResult:
        if self.PATTERN.search(data):
            return ValidationResult(False, data, ["xss"])
        return ValidationResult(True, html.escape(data))


class SQLRule(ValidationRule):
    PATTERN = re.compile(r"drop\s+table|delete\s+from|--", re.IGNORECASE)

    def validate(self, data: str) -> ValidationResult:
        if ";" in data and self.PATTERN.search(data):
            return ValidationResult(False, data, ["sql_injection"])
        return ValidationResult(True, data)


class SecurityValidator(CompositeValidator):
    """Validate input strings and file uploads."""

    def __init__(self, rules: Iterable[ValidationRule] | None = None) -> None:
        base_rules = list(rules or [XSSRule(), SQLRule()])
        super().__init__(base_rules)
        self.file_validator = FileValidator()

    def validate_input(self, value: str, field_name: str = "input") -> dict:
        result = self.validate(value)
        if not result.valid:
            raise ValidationError("; ".join(result.issues or []))
        return {"valid": True, "sanitized": result.sanitized or value}

    def validate_file_upload(self, filename: str, content: bytes) -> dict:
        result = self.file_validator.validate_file_upload(filename, content)
        if not result["valid"]:
            raise ValidationError("; ".join(result["issues"]))
        return result


__all__ = ["SecurityValidator", "XSSRule", "SQLRule", "FileValidator"]
