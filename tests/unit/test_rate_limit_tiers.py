import os

from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import DynamicConfigManager


def test_tiered_rate_limit_env_override(tmp_path, monkeypatch):
    yaml_text = """
security:
  rate_limits:
    free:
      requests: 100
      window_minutes: 1
      burst: 10
    pro:
      requests: 1000
      window_minutes: 1
"""
    path = tmp_path / "c.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    monkeypatch.setenv("YOSAI_CONFIG_FILE", str(path))
    required = {
        "SECRET_KEY": os.urandom(16).hex(),
        "DB_PASSWORD": os.urandom(16).hex(),
        "AUTH0_CLIENT_ID": "cid",
        "AUTH0_CLIENT_SECRET": os.urandom(16).hex(),
        "AUTH0_DOMAIN": "dom",
        "AUTH0_AUDIENCE": "aud",
    }
    for k, v in required.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("RATE_LIMIT_PRO_BURST", "50")
    cfg = DynamicConfigManager()
    assert cfg.get_rate_limit("free") == {"limit": 100, "window": 1, "burst": 10}
    assert cfg.get_rate_limit("pro")["burst"] == 50
