from __future__ import annotations

"""Central Unicode validation utilities."""

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable
import re
import unicodedata

import pandas as pd  # type: ignore[import]

from security.unicode_security_validator import (
    UnicodeSecurityValidator,
    UnicodeSecurityConfig,
)

_DANGEROUS_PREFIX_RE = re.compile(r"^[=+\-@]+")


@runtime_checkable
class UnicodeValidatorProtocol(Protocol):
    """Protocol for Unicode validation operations."""

    def validate_text(self, text: Any) -> str:
        """Return sanitized Unicode text."""

    def validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return ``df`` with all object columns sanitized."""


@dataclass
class UnicodeValidator(UnicodeValidatorProtocol):
    """Enterprise Unicode validator using :class:`UnicodeSecurityValidator`."""

    config: UnicodeSecurityConfig = UnicodeSecurityConfig()

    def __post_init__(self) -> None:
        self._validator = UnicodeSecurityValidator(config=self.config)

    # ------------------------------------------------------------------
    def validate_text(self, text: Any) -> str:
        sanitized = self._validator.validate_and_sanitize(text)
        try:
            sanitized = unicodedata.normalize(self.config.normalize_form, sanitized)
        except Exception:
            pass
        return _DANGEROUS_PREFIX_RE.sub("", sanitized)

    # ------------------------------------------------------------------
    def validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._validator.validate_dataframe(df)


__all__ = ["UnicodeValidator", "UnicodeValidatorProtocol"]
