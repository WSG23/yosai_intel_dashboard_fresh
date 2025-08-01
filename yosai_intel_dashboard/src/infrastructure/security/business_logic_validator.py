"""Placeholder business logic validator."""

from typing import Any

from yosai_intel_dashboard.src.core.exceptions import ValidationError


class BusinessLogicValidator:
    """Validate domain specific rules."""

    def validate(self, data: Any) -> Any:
        if data is None:
            raise ValidationError("Data cannot be None")
        return data
