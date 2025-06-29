from __future__ import annotations

"""Input validation utilities."""

import re
from typing import Any

from utils.unicode_handler import sanitize_unicode_input

from .validation_exceptions import ValidationError
from typing import Protocol

class Validator(Protocol):
    """Validator protocol"""

    def validate(self, data: Any) -> Any:
        ...

class InputValidator:
    """Simple input validator using unicode sanitization and basic patterns."""

    _dangerous_pattern = re.compile(r"[<>\"']")

    def validate(self, data: str) -> str:
        cleaned = sanitize_unicode_input(data)
        if self._dangerous_pattern.search(cleaned):
            raise ValidationError("Potentially dangerous characters detected")
        return cleaned
