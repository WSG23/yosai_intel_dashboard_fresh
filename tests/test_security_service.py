import pytest

from tests.fake_configuration import FakeConfiguration

fake_cfg = FakeConfiguration()
from services.data_processing.unified_file_validator import UnifiedFileValidator


def test_malicious_filename_is_invalid():
    validator = UnifiedFileValidator()
    result = validator.validate_file_meta("../../evil.csv", 10)
    assert result["valid"] is False
    assert any("Invalid filename" in issue for issue in result["issues"])


def test_oversized_upload_is_invalid():
    validator = UnifiedFileValidator()
    too_big = fake_cfg.security.max_upload_mb * 1024 * 1024 + 1
    result = validator.validate_file_meta("big.csv", too_big)
    assert result["valid"] is False
    assert any("File too large" in issue for issue in result["issues"])
