from __future__ import annotations

from typing import Any, Iterable

from .core import ValidationResult, Validator


class ValidationRule(Validator):
    """Base class for validation rules."""

    def validate(self, data: Any) -> ValidationResult:  # pragma: no cover - abstract
        raise NotImplementedError


class CompositeValidator(Validator):
    """Combine multiple validation rules."""

    def __init__(self, rules: Iterable[Validator] | None = None) -> None:
        self.rules = list(rules or [])

    def add_rule(self, rule: Validator) -> None:
        self.rules.append(rule)

    def validate(self, data: Any) -> ValidationResult:
        sanitized = data
        issues: list[str] = []
        for rule in self.rules:
            result = rule.validate(sanitized)
            sanitized = result.sanitized if result.sanitized is not None else sanitized
            if not result.valid:
                if result.issues:
                    issues.extend(result.issues)
                else:
                    issues.append("invalid")
        return ValidationResult(valid=not issues, sanitized=sanitized, issues=issues)
