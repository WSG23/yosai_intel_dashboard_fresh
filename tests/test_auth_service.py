import pytest

from core.exceptions import ValidationError
from yosai_intel_dashboard.src.services.data_processing.unified_upload_validator import (
    UnifiedUploadValidator,
)


def test_validator_methods_basic():
    validator = UnifiedUploadValidator()
    meta = validator.validate_file_meta("test.csv", 10)
    assert meta["valid"] is True
    with pytest.raises(ValidationError):
        validator.sanitize_filename("../bad.csv")


def test_filename_sanitization_surrogates_removed():
    validator = UnifiedUploadValidator()
    assert validator.sanitize_filename("good\ud800.csv") == "good.csv"


def test_filename_sanitization_valid():
    validator = UnifiedUploadValidator()
    assert validator.sanitize_filename("my_file.csv") == "my_file.csv"
