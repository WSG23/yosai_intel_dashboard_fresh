import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from flask import Flask, session

from yosai_intel_dashboard.src.core.protocols import ConfigurationProtocol

# Ensure project root is on path
sys.path.append(str(Path(__file__).resolve().parents[2]))


@dataclass
class FakeSecurityConfig:
    session_timeout: int = 3600
    session_timeout_by_role: Dict[str, int] = field(default_factory=dict)


class FakeConfiguration(ConfigurationProtocol):
    """Minimal configuration stub for session tests."""

    def __init__(self, security: FakeSecurityConfig | None = None) -> None:
        self.security = security or FakeSecurityConfig()

    def get_database_config(self) -> dict:
        return {}

    def get_app_config(self) -> dict:
        return {}

    def get_security_config(self) -> FakeSecurityConfig:
        return self.security

    def get_upload_config(self) -> dict:
        return {}

    def reload_config(self) -> None:
        pass

    def validate_config(self) -> dict:
        return {"valid": True}


from core.auth import User, _apply_session_timeout, _determine_session_timeout


def test_determine_session_timeout(monkeypatch):
    cfg = FakeConfiguration(
        FakeSecurityConfig(
            session_timeout=3600,
            session_timeout_by_role={"admin": 7200, "basic": 1800},
        )
    )
    monkeypatch.setattr("core.auth.get_security_config", cfg.get_security_config)
    assert _determine_session_timeout(["basic"]) == 1800
    assert _determine_session_timeout(["unknown"]) == 3600
    assert _determine_session_timeout(["admin", "basic"]) == 7200


def test_apply_session_timeout_sets_flask_values(monkeypatch):
    cfg = FakeConfiguration(
        FakeSecurityConfig(
            session_timeout=3600, session_timeout_by_role={"admin": 7200}
        )
    )
    monkeypatch.setattr("core.auth.get_security_config", cfg.get_security_config)
    app = Flask(__name__)
    # use a throwaway value rather than a real secret
    app.secret_key = os.urandom(16).hex()
    user = User("1", "Admin", "a@b.com", ["admin"])
    with app.app_context():
        with app.test_request_context():
            _apply_session_timeout(user)
            assert session.permanent is True
            assert app.permanent_session_lifetime.total_seconds() == 7200
