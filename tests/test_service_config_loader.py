from pathlib import Path

from yosai_intel_dashboard.src.infrastructure.config.config_loader import ServiceSettings, load_service_config


def test_load_service_config_defaults(monkeypatch):
    for var in [
        "REDIS_URL",
        "CACHE_TTL",
        "MODEL_DIR",
        "MODEL_REGISTRY_DB",
        "MODEL_REGISTRY_BUCKET",
        "MLFLOW_URI",
    ]:
        monkeypatch.delenv(var, raising=False)

    cfg = load_service_config()
    assert cfg.redis_url == ServiceSettings.redis_url
    assert cfg.cache_ttl == ServiceSettings.cache_ttl
    assert cfg.model_dir == ServiceSettings.model_dir
    assert cfg.registry_db == ServiceSettings.registry_db
    assert cfg.registry_bucket == ServiceSettings.registry_bucket
    assert cfg.mlflow_uri is None


def test_load_service_config_overrides(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://example:6380/1")
    monkeypatch.setenv("CACHE_TTL", "123")
    monkeypatch.setenv("MODEL_DIR", "/tmp/models")
    monkeypatch.setenv("MODEL_REGISTRY_DB", "sqlite:///test.db")
    monkeypatch.setenv("MODEL_REGISTRY_BUCKET", "bucket")
    monkeypatch.setenv("MLFLOW_URI", "http://mlflow")

    cfg = load_service_config()
    assert cfg.redis_url == "redis://example:6380/1"
    assert cfg.cache_ttl == 123
    assert cfg.model_dir == Path("/tmp/models")
    assert cfg.registry_db == "sqlite:///test.db"
    assert cfg.registry_bucket == "bucket"
    assert cfg.mlflow_uri == "http://mlflow"
