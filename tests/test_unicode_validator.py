from unicode_toolkit import UnicodeValidator


def test_unicode_validator_sanitizes_surrogates():
    validator = UnicodeValidator()
    text = "A" + "\ud800" + "B"
    result = validator.validate_and_sanitize(text)
    assert result == "AB"


def test_unicode_validator_strips_dangerous_chars():
    validator = UnicodeValidator()
    dangerous = "bad\u202Etext"
    sanitized = validator.validate_and_sanitize(dangerous)
    assert "\u202E" not in sanitized
