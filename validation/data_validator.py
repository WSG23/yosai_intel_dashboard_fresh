from __future__ import annotations

from typing import Iterable, Protocol

import pandas as pd

from .core import ValidationResult
from .rules import CompositeValidator, ValidationRule


class DataValidatorProtocol(Protocol):
    """Protocol for dataframe validators."""

    def validate_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        ...


class DataValidationRule(ValidationRule, Protocol):
    """Rule interface specialized for :class:`pandas.DataFrame`."""

    def validate(self, df: pd.DataFrame) -> ValidationResult:  # type: ignore[override]
        ...


class MissingColumnsRule(DataValidationRule):
    def __init__(self, required: Iterable[str]) -> None:
        self.required = list(required)

    def validate(self, df: pd.DataFrame) -> ValidationResult:  # type: ignore[override]
        missing = [c for c in self.required if c not in df.columns]
        if missing:
            return ValidationResult(False, df, [f"missing_columns:{','.join(missing)}"])
        return ValidationResult(True, df)


class EmptyDataRule(DataValidationRule):
    def validate(self, df: pd.DataFrame) -> ValidationResult:  # type: ignore[override]
        if df.empty:
            return ValidationResult(False, df, ["empty_dataframe"])
        return ValidationResult(True, df)


class SuspiciousColumnNameRule(DataValidationRule):
    def __init__(self, prefixes: Iterable[str] | None = None) -> None:
        self.prefixes = [p.lower() for p in (prefixes or ["=", "+", "-", "@", "cmd", "system"])]

    def validate(self, df: pd.DataFrame) -> ValidationResult:  # type: ignore[override]
        suspicious = [c for c in df.columns if any(str(c).lower().startswith(p) for p in self.prefixes)]
        if suspicious:
            return ValidationResult(False, df, [f"suspicious_column_names:{','.join(map(str, suspicious))}"])
        return ValidationResult(True, df)


class DataValidator(CompositeValidator, DataValidatorProtocol):
    """Validate pandas DataFrames using configurable rules."""

    def __init__(
        self,
        required_columns: Iterable[str] | None = None,
        suspicious_prefixes: Iterable[str] | None = None,
        extra_rules: Iterable[DataValidationRule] | None = None,
    ) -> None:
        rules: list[ValidationRule] = [EmptyDataRule()]
        if required_columns:
            rules.append(MissingColumnsRule(required_columns))
        rules.append(SuspiciousColumnNameRule(suspicious_prefixes))
        if extra_rules:
            rules.extend(extra_rules)
        super().__init__(rules)

    def validate_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        return self.validate(df)


__all__ = [
    "DataValidatorProtocol",
    "DataValidationRule",
    "MissingColumnsRule",
    "EmptyDataRule",
    "SuspiciousColumnNameRule",
    "DataValidator",
]
