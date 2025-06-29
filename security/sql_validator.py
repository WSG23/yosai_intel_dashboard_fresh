"""SQL injection prevention utilities."""

import re
from typing import Any

from .validation_exceptions import ValidationError

class SQLInjectionPrevention:
    """Basic SQL parameter validation."""

    _danger = re.compile(r"[;#]|--|/\*|\*/")

    @classmethod
    def validate_query_parameter(cls, value: Any) -> Any:
        text = str(value)
        if cls._danger.search(text):
            raise ValidationError("Suspicious characters in SQL parameter")
        return value
