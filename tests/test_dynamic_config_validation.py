from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import DynamicConfigManager


def test_invalid_yaml_types(tmp_path, monkeypatch):
    yaml_text = """
analytics:
  chunk_size: "oops"
uploads:
  DEFAULT_CHUNK_SIZE: 1000
"""
    path = tmp_path / "c.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    monkeypatch.setenv("YOSAI_CONFIG_FILE", str(path))
    monkeypatch.setenv("SECRET_KEY", "s")
    monkeypatch.setenv("DB_PASSWORD", "pwd")
    monkeypatch.setenv("AUTH0_CLIENT_ID", "cid")
    monkeypatch.setenv("AUTH0_CLIENT_SECRET", "secret")
    monkeypatch.setenv("AUTH0_DOMAIN", "dom")
    monkeypatch.setenv("AUTH0_AUDIENCE", "aud")

    cfg = DynamicConfigManager()
    # invalid chunk_size should not override default 50000
    assert cfg.analytics.chunk_size == 50000
    assert cfg.uploads.DEFAULT_CHUNK_SIZE == 1000
