import sys
import types


def _stub_optional_modules():
    """Provide minimal stubs for optional heavy dependencies."""
    sys.modules.setdefault("boto3", types.ModuleType("boto3"))
    sys.modules.setdefault("hvac", types.ModuleType("hvac"))
    sys.modules.setdefault("cryptography", types.ModuleType("cryptography"))
    sys.modules.setdefault("confluent_kafka", types.ModuleType("confluent_kafka"))


def test_environment_processor_applied(monkeypatch, tmp_path):
    cfg_text = """
app:
  host: localhost
  port: 8000
database:
  host: db.local
security:
  secret_key: default
"""
    path = tmp_path / "config.yaml"
    path.write_text(cfg_text, encoding="utf-8")

    monkeypatch.setenv("YOSAI_DATABASE_HOST", "db.example.com")
    monkeypatch.setenv("YOSAI_PORT", "9000")
    monkeypatch.setenv("SECRET_KEY", "envsecret")

    _stub_optional_modules()
    from config.unified_loader import UnifiedLoader

    loader = UnifiedLoader(str(path))
    cfg = loader.load()

    assert cfg.database.host == "db.example.com"
    assert cfg.app.port == 9000
    assert cfg.app.secret_key == "envsecret"
