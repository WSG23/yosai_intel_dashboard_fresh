from yosai_intel_dashboard.src.infrastructure.security.unicode_security_validator import (
    UnicodeSecurityValidator as UnicodeValidator,
)


def test_unicode_validator_sanitizes_surrogates():
    validator = UnicodeValidator()
    text = "A" + "\ud800" + "B"
    result = validator.validate_and_sanitize(text)
    assert result == "AB"


def test_unicode_validator_strips_dangerous_chars():
    validator = UnicodeValidator()
    dangerous = "bad\u202etext"
    sanitized = validator.validate_and_sanitize(dangerous)
    assert "\u202e" not in sanitized
