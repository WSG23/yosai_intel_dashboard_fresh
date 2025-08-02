from __future__ import annotations

import html
import json
import os
import re
from typing import Callable, Iterable, Mapping

from yosai_intel_dashboard.src.core.exceptions import ValidationError

from .core import ValidationResult
from .file_validator import FileValidator
from .rules import CompositeValidator, ValidationRule

# Import dynamically inside methods to avoid circular imports during module init


def _regex_validator(
    pattern: re.Pattern[str], issue: str
) -> Callable[[str], ValidationResult]:
    def _validate(data: str) -> ValidationResult:
        if pattern.search(data):
            return ValidationResult(False, data, [issue])
        return ValidationResult(True, data)

    return _validate


def _json_validator(data: str) -> ValidationResult:
    try:
        parsed = json.loads(data)
    except Exception:
        return ValidationResult(False, data, ["json"])
    return ValidationResult(True, json.dumps(parsed, ensure_ascii=False))


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
        self._type_validators: Mapping[str, Callable[[str], ValidationResult]] = {
            "sql": _regex_validator(SQLRule.PATTERN, "sql_injection"),
            "nosql": _regex_validator(
                re.compile(r"\$(where|gt|lt|ne|eq|or)", re.IGNORECASE),
                "nosql_injection",
            ),
            "ldap": _regex_validator(
                re.compile(r"[\*\(\)\|&]", re.IGNORECASE),
                "ldap_injection",
            ),
            "xpath": _regex_validator(
                re.compile(r"[\"']\s*or\s*[\"']1\s*=\s*[\"']1", re.IGNORECASE),
                "xpath_injection",
            ),
            "command": _regex_validator(
                re.compile(r"[;&|`]"),
                "command_injection",
            ),
            "html": lambda v: ValidationResult(True, html.escape(v)),
            "json": _json_validator,
        }

    def sanitize_filename(self, filename: str) -> str:
        """Return a safe filename stripped of path components."""
        name = os.path.basename(filename)
        if not name or name in {".", ".."}:
            raise ValidationError("Invalid filename")
        return name

    def validate_file_meta(self, filename: str, size_bytes: int) -> dict:
        """Validate filename and size limits without reading contents."""
        issues: list[str] = []
        try:
            sanitized = self.sanitize_filename(filename)
        except ValidationError:
            issues.append("Invalid filename")
            sanitized = os.path.basename(filename)

        # Import here to avoid circular dependencies during initialization
        from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
            dynamic_config,
        )

        max_bytes = dynamic_config.security.max_upload_mb * 1024 * 1024
        if size_bytes > max_bytes:
            issues.append("File too large")

        return {"valid": not issues, "issues": issues, "filename": sanitized}

    def validate_input(
        self, value: str, field_name: str = "input", *, input_type: str | None = None
    ) -> dict:
        if input_type:
            validator = self._type_validators.get(input_type)
            if validator:
                specialized = validator(value)
                if not specialized.valid:
                    raise ValidationError("; ".join(specialized.issues or []))
                value = specialized.sanitized or value
        result = self.validate(value)
        if not result.valid:
            raise ValidationError("; ".join(result.issues or []))
        return {"valid": True, "sanitized": result.sanitized or value}

    def validate_file_upload(self, filename: str, content: bytes) -> dict:
        result = self.file_validator.validate_file_upload(filename, content)
        if not result["valid"]:
            raise ValidationError("; ".join(result["issues"]))
        return result


__all__ = [
    "SecurityValidator",
    "XSSRule",
    "SQLRule",
    "FileValidator",
]
