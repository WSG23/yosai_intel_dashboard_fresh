from __future__ import annotations

"""Validator for Unicode surrogate characters."""

import logging
from dataclasses import dataclass
from typing import Any

from core.exceptions import ValidationError
from core.unicode import contains_surrogates
from services.security_callback_controller import SecurityEvent, emit_security_event


@dataclass
class SurrogateHandlingConfig:
    """Configuration for :class:`UnicodeSurrogateValidator`."""

    mode: str = "remove"
    replacement: str = ""


class UnicodeSurrogateValidator:
    """Validate or sanitize text for surrogate characters."""

    def __init__(self, config: SurrogateHandlingConfig | None = None) -> None:
        self.config = config or SurrogateHandlingConfig()
        self.logger = logging.getLogger(__name__)

        if contains_surrogates(self.config.replacement):
            raise ValueError("Replacement string cannot include surrogate code points")

    def sanitize(self, value: Any) -> str:
        """Return ``value`` with surrogates handled according to configuration."""
        if not isinstance(value, str):
            value = str(value)

        if not contains_surrogates(value):
            return value

        emit_security_event(
            SecurityEvent.VALIDATION_FAILED, {"issue": "unicode_surrogates"}
        )

        if self.config.mode == "strict":
            raise ValidationError("Surrogate characters not allowed")

        replacement = self.config.replacement if self.config.mode == "replace" else ""
        cleaned = "".join(
            ch if not (0xD800 <= ord(ch) <= 0xDFFF) else replacement for ch in value
        )
        return cleaned


__all__ = [
    "UnicodeSurrogateValidator",
    "SurrogateHandlingConfig",
    "contains_surrogates",
]
