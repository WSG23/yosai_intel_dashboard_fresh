from __future__ import annotations

"""Security validation utilities.

This module exposes :class:`SecurityValidator` which can optionally incorporate
an anomaly detection model such as scikit-learn's ``IsolationForest``. The model
must implement a ``predict`` method returning ``1`` for normal inputs and ``-1``
for anomalies.

Example
-------
>>> from sklearn.ensemble import IsolationForest
>>> from validation.security_validator import SecurityValidator
>>> model = IsolationForest().fit([[1], [2], [3]])
>>> validator = SecurityValidator(anomaly_model=model)
>>> validator.validate_input("hello")  # doctest: +SKIP
{"valid": True, "sanitized": "hello"}
"""

import html
import json
import os
import re
from typing import Any, Iterable


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

    def __init__(
        self,
        rules: Iterable[ValidationRule] | None = None,
        anomaly_model: Any | None = None,
    ) -> None:
        base_rules = list(rules or [XSSRule(), SQLRule()])
        super().__init__(base_rules)
        self.file_validator = FileValidator()
        self.anomaly_model = anomaly_model

    def _anomaly_check(self, value: str, field_name: str) -> None:
        """Score ``value`` with ``anomaly_model`` if provided."""

        if not self.anomaly_model:
            return
        try:
            prediction = self.anomaly_model.predict([[len(value)]])
        except Exception as exc:  # pragma: no cover - defensive
            raise ValidationError("Anomaly check failed") from exc
        if prediction[0] == -1:
            raise ValidationError(f"Anomalous input detected in {field_name}")


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

    def validate_input(self, value: str, field_name: str = "input") -> dict:
        self._anomaly_check(value, field_name)

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
