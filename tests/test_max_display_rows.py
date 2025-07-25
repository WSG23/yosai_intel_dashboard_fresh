import pandas as pd

from tests.fake_configuration import FakeConfiguration
from yosai_intel_dashboard.src.infrastructure.config import create_config_manager

fake_cfg = FakeConfiguration()
from yosai_intel_dashboard.src.infrastructure.config.constants import MAX_DISPLAY_ROWS
from yosai_intel_dashboard.src.services.data_processing.file_processor import (
    create_file_preview,
)


def test_dynamic_config_default_display_rows():
    assert fake_cfg.analytics.max_display_rows == 10000


def test_config_manager_loads_max_display_rows(tmp_path, monkeypatch):
    yaml = """
app:
  title: Test
database:
  name: test.db
security:
  secret_key: test
analytics:
  max_display_rows: 123
"""
    path = tmp_path / "config.yaml"
    path.write_text(yaml)
    envs = {
        "SECRET_KEY": "x",
        "DB_PASSWORD": "x",
        "AUTH0_CLIENT_ID": "x",
        "AUTH0_CLIENT_SECRET": "x",
        "AUTH0_DOMAIN": "x",
        "AUTH0_AUDIENCE": "x",
    }
    for k, v in envs.items():
        monkeypatch.setenv(k, v)
    cfg = create_config_manager(str(path))
    assert cfg.get_analytics_config().max_display_rows == 123


def test_create_file_preview_respects_limit():
    df = pd.DataFrame({"a": range(MAX_DISPLAY_ROWS + 50)})
    preview = create_file_preview(df, max_rows=MAX_DISPLAY_ROWS + 20)
    assert len(preview["preview_data"]) == MAX_DISPLAY_ROWS
