import pytest

from services.data_processing.unified_file_validator import UnifiedFileValidator
from core.exceptions import ValidationError


def test_validator_methods_basic():
    validator = UnifiedFileValidator()
    meta = validator.validate_file_meta("test.csv", 10)
    assert meta["valid"] is True
    with pytest.raises(ValidationError):
        validator.sanitize_filename("../bad.csv")
