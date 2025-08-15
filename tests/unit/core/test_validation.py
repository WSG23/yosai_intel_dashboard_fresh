import pandas as pd
import pytest
import six
import bleach

from validation.security_validator import SecurityValidator
from validation.unicode_validator import UnicodeValidator
from yosai_intel_dashboard.src.core.exceptions import ValidationError
from yosai_intel_dashboard.src.infrastructure.security.business_logic_validator import (
    BusinessLogicValidator,
)
from yosai_intel_dashboard.src.infrastructure.security.unicode_security_validator import (
    UnicodeSecurityConfig,
)
from yosai_intel_dashboard.src.infrastructure.security.xss_validator import (
    XSSPrevention,
)

if not hasattr(six.moves.http_client, "HTTPResponse"):
    class _DummyResponse:  # pragma: no cover - simple placeholder
        pass

    six.moves.http_client.HTTPResponse = _DummyResponse  # type: ignore[attr-defined]

# ----------------------------------------------------------------------
# SecurityValidator validate_input / XSSPrevention.sanitize_html_output
# ----------------------------------------------------------------------


def test_validate_input_valid():
    validator = SecurityValidator()
    result = validator.validate_input("safe text")
    assert result == {"valid": True, "sanitized": "safe text"}


def test_validate_input_invalid():
    validator = SecurityValidator()
    with pytest.raises(ValidationError):
        validator.validate_input("<script>alert('x')</script>")


def test_validate_output_valid(monkeypatch):
    monkeypatch.setattr(bleach, "clean", lambda text, **_: text)
    html = "<b>bold</b>"
    assert XSSPrevention.sanitize_html_output(html) == html


def test_validate_output_invalid(monkeypatch):
    def fake_clean(text: str, **_: object) -> str:
        return text.replace("<script>alert('x')</script>", "")

    monkeypatch.setattr(bleach, "clean", fake_clean)
    unsafe = "<b>bold</b><script>alert('x')</script>"
    result = XSSPrevention.sanitize_html_output(unsafe)
    assert result == "<b>bold</b>"


# ----------------------------------------------------------------------
# UnicodeValidator
# ----------------------------------------------------------------------


def test_unicode_validator_text():
    validator = UnicodeValidator(UnicodeSecurityConfig(strict_mode=False))
    text = "A\ud800B"
    assert validator.validate_text(text) == "AB"


def test_unicode_validator_dataframe():
    validator = UnicodeValidator(UnicodeSecurityConfig(strict_mode=False))
    df = pd.DataFrame({"col": ["bad\u202e", "ok"]})
    cleaned = validator.validate_dataframe(df)
    assert "\u202e" not in cleaned.iloc[0, 0]
    assert cleaned.iloc[0, 0] == "bad"


# ----------------------------------------------------------------------
# BusinessLogicValidator
# ----------------------------------------------------------------------


def test_business_validator_valid():
    validator = BusinessLogicValidator()
    assert validator.validate("data") == "data"


def test_business_validator_invalid():
    validator = BusinessLogicValidator()
    with pytest.raises(ValidationError):
        validator.validate(None)
