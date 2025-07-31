import os
import sys
import types


def _stub_optional_modules():
    """Provide minimal stubs for optional heavy dependencies."""
    sys.modules.setdefault("boto3", types.ModuleType("boto3"))
    sys.modules.setdefault("hvac", types.ModuleType("hvac"))
    sys.modules.setdefault("cryptography", types.ModuleType("cryptography"))
    sys.modules.setdefault("confluent_kafka", types.ModuleType("confluent_kafka"))


def test_environment_processor_applied(monkeypatch, tmp_path):
    secret = os.urandom(16).hex()
    cfg_text = f"""
app:
  host: localhost
  port: 8000
database:
  host: db.local
security:
  secret_key: {secret}
"""
    path = tmp_path / "config.yaml"
    path.write_text(cfg_text, encoding="utf-8")

    monkeypatch.setenv("YOSAI_DATABASE_HOST", "db.example.com")
    monkeypatch.setenv("YOSAI_PORT", "9000")
    env_secret = os.urandom(16).hex()
    monkeypatch.setenv("SECRET_KEY", env_secret)

    _stub_optional_modules()
    from yosai_intel_dashboard.src.infrastructure.config.unified_loader import UnifiedLoader

    loader = UnifiedLoader(str(path))
    cfg = loader.load()

    assert cfg.database.host == "db.example.com"
    assert cfg.app.port == 9000
    assert cfg.app.secret_key == env_secret
