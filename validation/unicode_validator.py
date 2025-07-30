"""Unicode validation protocol and default implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import pandas as pd

from security.unicode_security_validator import (
    UnicodeSecurityConfig,
    UnicodeSecurityValidator,
)


class UnicodeValidatorProtocol(Protocol):
    """Protocol for Unicode validation operations."""

    def validate_text(self, text: Any) -> str:
        """Return sanitized ``text``."""

    def validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return sanitized copy of ``df``."""


@dataclass
class UnicodeValidator(UnicodeValidatorProtocol):
    """Concrete Unicode validator using :class:`UnicodeSecurityValidator`."""

    validator: UnicodeSecurityValidator

    def __init__(self, config: UnicodeSecurityConfig | None = None) -> None:
        self.validator = UnicodeSecurityValidator(config=config)

    def validate_text(self, text: Any) -> str:
        return self.validator.validate_and_sanitize(text)

    def validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.validator.validate_dataframe(df)


__all__ = ["UnicodeValidator", "UnicodeValidatorProtocol"]
