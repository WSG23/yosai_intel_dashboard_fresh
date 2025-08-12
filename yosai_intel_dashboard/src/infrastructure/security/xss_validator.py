"""Cross-site scripting prevention utilities."""

import bleach

from yosai_intel_dashboard.src.core.exceptions import ValidationError


SAFE_TAGS = ["b", "i", "em", "strong", "a"]
SAFE_ATTRS = {"a": ["href", "title"]}


class XSSPrevention:
    """Provides HTML sanitization"""

    @staticmethod
    def sanitize_html_output(value: str) -> str:
        if not isinstance(value, str):
            raise ValidationError("Expected string for HTML sanitization")
        return bleach.clean(value, tags=SAFE_TAGS, attributes=SAFE_ATTRS, strip=True)
