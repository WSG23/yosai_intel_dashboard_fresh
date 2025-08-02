import pandas as pd
import pytest

from yosai_intel_dashboard.src.core.exceptions import ValidationError
from security.business_logic_validator import BusinessLogicValidator
from security.unicode_security_validator import UnicodeSecurityConfig
from security.xss_validator import XSSPrevention
from validation.security_validator import SecurityValidator
from validation.unicode_validator import UnicodeValidator

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


def test_validate_output_valid():
    assert XSSPrevention.sanitize_html_output("hello") == "hello"


def test_validate_output_invalid():
    result = XSSPrevention.sanitize_html_output("<script>alert('x')</script>")
    assert "<" not in result and ">" not in result


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
