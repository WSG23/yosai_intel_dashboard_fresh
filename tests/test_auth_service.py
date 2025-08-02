import sys
from types import SimpleNamespace

import pytest
from tests.import_helpers import safe_import, import_optional

stub_dynamic_config = SimpleNamespace(
    security=SimpleNamespace(max_upload_mb=10),
    upload=SimpleNamespace(allowed_file_types=[".csv", ".json", ".xlsx", ".xls"]),
)
safe_import('config.dynamic_config', SimpleNamespace()
    dynamic_config=stub_dynamic_config
)

from core.exceptions import ValidationError
from validation.security_validator import SecurityValidator


def test_validator_methods_basic():
    validator = SecurityValidator()
    result = validator.validate_input("safe text", "comment")
    assert result["valid"] is True
    with pytest.raises(ValidationError):
        validator.validate_input("DROP TABLE users; --", "comment")


def test_filename_sanitization_surrogates_removed():
    validator = SecurityValidator()
    sanitized = validator.validate_input("good\ud800.csv")["sanitized"]
    assert sanitized == "good\ud800.csv"


def test_filename_sanitization_valid():
    validator = SecurityValidator()
    sanitized = validator.validate_input("my_file.csv")["sanitized"]
    assert sanitized == "my_file.csv"
