import pytest

from core.exceptions import ValidationError
from validation.security_validator import SecurityValidator


def test_validator_methods_basic():
    validator = SecurityValidator()
    meta = validator.validate_file_meta("test.csv", 10)
    assert meta["valid"] is True
    with pytest.raises(ValidationError):
        validator.sanitize_filename("../bad.csv")


def test_filename_sanitization_surrogates_removed():
    validator = SecurityValidator()
    assert validator.sanitize_filename("good\ud800.csv") == "good.csv"


def test_filename_sanitization_valid():
    validator = SecurityValidator()
    assert validator.sanitize_filename("my_file.csv") == "my_file.csv"
