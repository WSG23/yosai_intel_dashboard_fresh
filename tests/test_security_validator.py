import pytest

from core.security_validator import SecurityLevel, SecurityValidator


def test_sql_injection_validation():
    validator = SecurityValidator()
    issues = validator._validate_sql_injection("' OR 1=1 --", "username")
    assert issues
    assert issues[0].level == SecurityLevel.CRITICAL


def test_main_validation_orchestration():
    validator = SecurityValidator()
    result = validator.validate_input("<script>alert('xss')</script>", "comment")
    assert not result["valid"]
    assert result["issues"]
    assert "sanitized" in result
