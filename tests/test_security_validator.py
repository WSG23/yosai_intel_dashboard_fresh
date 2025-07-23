import types

import security_callback_controller
from core.security_validator import (
    AdvancedSQLValidator,
    SecurityLevel,
    SecurityValidator,
)


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


def test_check_permissions_allows():
    class FakeSession:
        def get(self, url, params=None, headers=None, timeout=None):
            class Resp:
                def raise_for_status(self):
                    pass

                def json(self):
                    return {"allowed": True}

            return Resp()

    session = FakeSession()
    validator = SecurityValidator()
    assert validator.check_permissions("alice", "door1", "open", client=session) is True


def test_check_permissions_denied():
    class FakeSession:
        def get(self, url, params=None, headers=None, timeout=None):
            class Resp:
                def raise_for_status(self):
                    pass

                def json(self):
                    return {"allowed": False}

            return Resp()

    session = FakeSession()
    validator = SecurityValidator()
    assert (
        validator.check_permissions("alice", "door1", "open", client=session) is False
    )
