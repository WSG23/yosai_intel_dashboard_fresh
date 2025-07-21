import types
import pytest

from core.security_validator import (
    AdvancedSQLValidator,
    SecurityLevel,
    SecurityValidator,
)
import security_callback_controller


def test_sql_injection_validation():
    validator = SecurityValidator()
    issues = validator._validate_sql_injection("' OR 1=1 --", "username")
    assert issues
    assert issues[0].level == SecurityLevel.CRITICAL


def test_valid_sql_passes():
    validator = AdvancedSQLValidator()
    assert not validator.is_malicious("SELECT * FROM users WHERE id = 1")


def test_main_validation_orchestration():
    # Stub security callback handling for isolated testing
    security_callback_controller.security_unified_callbacks = types.SimpleNamespace(
        trigger=lambda *args, **kwargs: None
    )

    validator = SecurityValidator()
    result = validator.validate_input("<script>alert('xss')</script>", "comment")
    assert not result["valid"]
    assert result["issues"]
    assert "sanitized" in result


def test_check_permissions_allows(tmp_path, monkeypatch):
    perm_file = tmp_path / "perms.json"
    perm_file.write_text('{"alice": {"door1": "Granted"}}')
    monkeypatch.setenv("PERMISSIONS_FILE", str(perm_file))
    validator = SecurityValidator()
    assert validator.check_permissions("alice", "door1", "open") is True


def test_check_permissions_denied(tmp_path, monkeypatch):
    perm_file = tmp_path / "perms.json"
    perm_file.write_text('{"alice": {"door1": "Denied"}}')
    monkeypatch.setenv("PERMISSIONS_FILE", str(perm_file))
    validator = SecurityValidator()
    assert validator.check_permissions("alice", "door1", "open") is False
