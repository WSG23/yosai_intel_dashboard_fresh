import sys
from pathlib import Path
import types
from dataclasses import dataclass, field
from typing import Dict
from flask import Flask, session

# Ensure project root is on path
sys.path.append(str(Path(__file__).resolve().parents[2]))

@dataclass
class SecurityConfig:
    session_timeout: int = 3600
    session_timeout_by_role: Dict[str, int] = field(default_factory=dict)

def _setup_fake_config(cfg):
    pkg = types.ModuleType("config")
    sub = types.ModuleType("config.config")
    sub.get_security_config = lambda: cfg
    pkg.config = sub
    sys.modules["config"] = pkg
    sys.modules["config.config"] = sub

_setup_fake_config(SecurityConfig())
from core.auth import User, _determine_session_timeout, _apply_session_timeout


def test_determine_session_timeout(monkeypatch):
    cfg = SecurityConfig(session_timeout=3600,
                         session_timeout_by_role={"admin": 7200, "basic": 1800})
    monkeypatch.setattr("core.auth.get_security_config", lambda: cfg)
    assert _determine_session_timeout(["basic"]) == 1800
    assert _determine_session_timeout(["unknown"]) == 3600
    assert _determine_session_timeout(["admin", "basic"]) == 7200


def test_apply_session_timeout_sets_flask_values(monkeypatch):
    cfg = SecurityConfig(session_timeout=3600,
                         session_timeout_by_role={"admin": 7200})
    monkeypatch.setattr("core.auth.get_security_config", lambda: cfg)
    app = Flask(__name__)
    app.secret_key = "x"
    user = User("1", "Admin", "a@b.com", ["admin"])
    with app.app_context():
        with app.test_request_context():
            _apply_session_timeout(user)
            assert session.permanent is True
            assert app.permanent_session_lifetime.total_seconds() == 7200
