import logging
import sys
import types

import pytest


class ValidationError(Exception):
    pass


class TemporaryBlockError(Exception):
    pass


class PermanentBanError(Exception):
    pass


class ConfigurationError(Exception):
    pass


core_exceptions = types.ModuleType("yosai_intel_dashboard.src.core.exceptions")
core_exceptions.ValidationError = ValidationError
core_exceptions.TemporaryBlockError = TemporaryBlockError
core_exceptions.PermanentBanError = PermanentBanError
core_exceptions.ConfigurationError = ConfigurationError
sys.modules.setdefault("yosai_intel_dashboard.src.core", types.ModuleType("core"))
sys.modules["yosai_intel_dashboard.src.core.exceptions"] = core_exceptions

security_stub = types.ModuleType("security")
unicode_security_validator = types.ModuleType("security.unicode_security_validator")
unicode_security_validator.UnicodeSecurityValidator = object
unicode_security_validator.UnicodeSecurityConfig = object
security_stub.unicode_security_validator = unicode_security_validator
security_stub.secrets_validator = types.SimpleNamespace(
    SecretsValidator=object, register_health_endpoint=lambda *a, **k: None
)
sys.modules["security"] = security_stub
sys.modules["security.unicode_security_validator"] = unicode_security_validator

file_validator_stub = types.ModuleType(
    "yosai_intel_dashboard.src.infrastructure.validation.file_validator"
)


class DummyFileValidator:
    def validate_file_upload(self, *a, **k):  # pragma: no cover - simple stub
        return {"valid": True}


file_validator_stub.FileValidator = DummyFileValidator
sys.modules[
    "yosai_intel_dashboard.src.infrastructure.validation.file_validator"
] = file_validator_stub

from yosai_intel_dashboard.src.infrastructure.validation.security_validator import (
    SecurityValidator,
)


def test_sql_injection_validation():
    validator = SecurityValidator(rate_limit=1, window_seconds=60)
    with pytest.raises(Exception):
        validator.validate_input("1; DROP TABLE users")


def test_main_validation_orchestration():
    validator = SecurityValidator(rate_limit=1, window_seconds=60)
    value = "<script>alert('xss')</script>"
    with pytest.raises(Exception):
        validator.validate_input(value, "comment")


@pytest.mark.skip("File upload validation not covered in this test")
def test_validate_file_upload_rules():
    validator = SecurityValidator(rate_limit=1, window_seconds=60)
    valid = validator.validate_file_upload("ok.csv", b"a,b\n1,2")
    assert valid["valid"]


class RedisMock:
    def __init__(self) -> None:
        self.store: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    def expire(self, key: str, _seconds: int) -> None:
        pass


def test_rate_limit_escalation(caplog: pytest.LogCaptureFixture) -> None:
    redis = RedisMock()
    validator = SecurityValidator(redis_client=redis, rate_limit=1, window_seconds=60)
    identifier = "user1"

    validator.validate_input("safe", identifier=identifier)

    with caplog.at_level(logging.WARNING):
        validator.validate_input("safe", identifier=identifier)
        assert "Rate limit exceeded" in caplog.text

        caplog.clear()
        with pytest.raises(TemporaryBlockError):
            validator.validate_input("safe", identifier=identifier)
        assert "Temporary block" in caplog.text

        caplog.clear()
        with pytest.raises(PermanentBanError):
            validator.validate_input("safe", identifier=identifier)
        assert "Permanent ban" in caplog.text
