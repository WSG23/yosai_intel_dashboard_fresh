import pytest

from tests.config import FakeConfiguration
from tests.import_helpers import safe_import, import_optional

fake_cfg = FakeConfiguration()
from validation.security_validator import SecurityValidator


def test_malicious_filename_is_invalid():
    validator = SecurityValidator()
    result = validator.validate_file_meta("../../evil.csv", 10)
    assert result["valid"] is False
    assert any("Invalid filename" in issue for issue in result["issues"])


def test_oversized_upload_is_invalid():
    validator = SecurityValidator()
    too_big = fake_cfg.security.max_upload_mb * 1024 * 1024 + 1
    result = validator.validate_file_meta("big.csv", too_big)
    assert result["valid"] is False
    assert any("File too large" in issue for issue in result["issues"])


def test_sanitize_filename_strips_path_components():
    validator = SecurityValidator()
    sanitized = validator.sanitize_filename("../foo/bar.csv")
    assert sanitized == "bar.csv"
