from datetime import datetime, timedelta

from yosai_intel_dashboard.src.core.secret_manager import SecretsManager
from yosai_intel_dashboard.src.core.secrets_validator import SecretsValidator


class DummyManager(SecretsManager):
    def get(self, key: str, default=None):  # type: ignore[override]
        return "x" * 32


def test_flags_stale_secret(monkeypatch):
    validator = SecretsValidator(DummyManager())
    old = (datetime.utcnow() - timedelta(days=91)).isoformat()
    monkeypatch.setenv("SECRET_KEY_LAST_ROTATED", old)
    invalid = validator.validate_production_secrets()
    assert "SECRET_KEY" in invalid
