import pytest

from security.auth_service import SecurityService
from config.dynamic_config import dynamic_config


def test_malicious_filename_is_invalid():
    service = SecurityService(None)
    service.enable_file_validation()
    result = service.validate_file("../../evil.csv", 10)
    assert result["valid"] is False
    assert any("Invalid filename" in issue for issue in result["issues"])


def test_oversized_upload_is_invalid():
    service = SecurityService(None)
    service.enable_file_validation()
    too_big = dynamic_config.security.max_upload_mb * 1024 * 1024 + 1
    result = service.validate_file("big.csv", too_big)
    assert result["valid"] is False
    assert any("File too large" in issue for issue in result["issues"])
