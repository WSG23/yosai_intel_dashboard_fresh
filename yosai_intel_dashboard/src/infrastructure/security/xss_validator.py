"""Cross-site scripting prevention utilities."""

import html

from yosai_intel_dashboard.src.core.exceptions import ValidationError


class XSSPrevention:
    """Provides HTML sanitization"""

    @staticmethod
    def sanitize_html_output(value: str) -> str:
        if not isinstance(value, str):
            raise ValidationError("Expected string for HTML sanitization")
        return html.escape(value)
