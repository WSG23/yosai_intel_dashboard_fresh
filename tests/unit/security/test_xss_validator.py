import html
import pytest

from yosai_intel_dashboard.src.core.exceptions import ValidationError
from yosai_intel_dashboard.src.infrastructure.security.xss_validator import XSSPrevention


def test_sanitize_html_output_escapes_script_tag():
    text = "<script>alert('xss')</script>"
    sanitized = XSSPrevention.sanitize_html_output(text)
    assert sanitized == html.escape(text)


def test_sanitize_html_output_rejects_non_string():
    with pytest.raises(ValidationError):
        XSSPrevention.sanitize_html_output(123)
