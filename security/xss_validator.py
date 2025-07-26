"""Cross-site scripting prevention utilities."""

import html

from core.exceptions import ValidationError


class XSSPrevention:
    """Provides HTML sanitization"""

    @staticmethod
    def sanitize_html_output(value: str) -> str:
        if not isinstance(value, str):
            raise ValidationError("value", "Expected string for HTML sanitization", "invalid_type")
        return html.escape(value)
