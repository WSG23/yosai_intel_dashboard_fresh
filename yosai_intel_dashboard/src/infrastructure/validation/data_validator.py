from __future__ import annotations

import re
from typing import Iterable, Pattern, Protocol

import pandas as pd

from .core import ValidationResult
from .rules import CompositeValidator, ValidationRule


class DataValidatorProtocol(Protocol):
    """Protocol for DataFrame validators."""

    def validate_dataframe(self, df: pd.DataFrame) -> ValidationResult: ...


class EmptyDataRule(ValidationRule):
    """Fail if the DataFrame is empty."""

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        if df.empty:
            return ValidationResult(False, df, ["empty_dataframe"])
        return ValidationResult(True, df)


class MissingColumnsRule(ValidationRule):
    """Ensure required columns are present."""

    def __init__(self, required: Iterable[str]) -> None:
        self.required = list(required)

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        missing = [c for c in self.required if c not in df.columns]
        if missing:
            issue = f"missing_columns:{','.join(missing)}"
            return ValidationResult(False, df, [issue])
        return ValidationResult(True, df)


class SuspiciousColumnNameRule(ValidationRule):
    """Detect suspicious column names that may indicate malicious input."""

    DEFAULT_PATTERN = re.compile(r"(?i)^(?:=|\+|-|@)|cmd|system|drop|delete|exec")

    def __init__(self, pattern: Pattern[str] | None = None) -> None:
        self.pattern = pattern or self.DEFAULT_PATTERN

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        suspicious = [c for c in df.columns if self.pattern.search(str(c))]
        if suspicious:
            issue = f"suspicious_columns:{','.join(map(str, suspicious))}"
            return ValidationResult(False, df, [issue])
        return ValidationResult(True, df)


class DataValidator(CompositeValidator):
    """Validate DataFrames for analytics modules."""

    def __init__(
        self,
        required_columns: Iterable[str] | None = None,
        rules: Iterable[ValidationRule] | None = None,
        suspicious_pattern: Pattern[str] | None = None,
    ) -> None:
        base_rules = list(rules or [])
        if required_columns:
            base_rules.append(MissingColumnsRule(required_columns))
        base_rules.append(EmptyDataRule())
        base_rules.append(SuspiciousColumnNameRule(suspicious_pattern))
        super().__init__(base_rules)

    def validate_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        return self.validate(df)


__all__ = [
    "DataValidator",
    "DataValidatorProtocol",
    "EmptyDataRule",
    "MissingColumnsRule",
    "SuspiciousColumnNameRule",
]
