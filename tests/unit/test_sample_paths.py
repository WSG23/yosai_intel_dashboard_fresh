import os

from yosai_intel_dashboard.src.infrastructure.config import get_config, reload_config
from yosai_intel_dashboard.src.services import AnalyticsService


def test_fixed_processor_paths_from_env(monkeypatch):
    """Paths should come from environment variables when set."""

    monkeypatch.setenv("SAMPLE_CSV_PATH", "/tmp/env_sample.csv")
    monkeypatch.setenv("SAMPLE_JSON_PATH", "/tmp/env_sample.json")

    calls = []

    def fake_exists(path):
        calls.append(path)
        return False

    monkeypatch.setattr(os.path, "exists", fake_exists)

    service = AnalyticsService()
    service._get_analytics_with_fixed_processor()

    assert "/tmp/env_sample.csv" in calls
    assert "/tmp/env_sample.json" in calls


def test_fixed_processor_paths_from_config(monkeypatch):
    """Service should fallback to config when env vars are absent."""

    monkeypatch.delenv("SAMPLE_CSV_PATH", raising=False)
    monkeypatch.delenv("SAMPLE_JSON_PATH", raising=False)

    cfg = reload_config()  # fresh config
    cfg.config.sample_files.csv_path = "/tmp/config_sample.csv"
    cfg.config.sample_files.json_path = "/tmp/config_sample.json"

    calls = []

    def fake_exists(path):
        calls.append(path)
        return False

    monkeypatch.setattr(os.path, "exists", fake_exists)

    service = AnalyticsService()
    service._get_analytics_with_fixed_processor()

    assert "/tmp/config_sample.csv" in calls
    assert "/tmp/config_sample.json" in calls
