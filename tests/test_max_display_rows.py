from __future__ import annotations

import os

import pandas as pd

from config import create_config_manager
from tests.config import FakeConfiguration
from tests.import_helpers import safe_import, import_optional

fake_cfg = FakeConfiguration()
from yosai_intel_dashboard.src.infrastructure.config.constants import MAX_DISPLAY_ROWS
from yosai_intel_dashboard.src.file_processing import create_file_preview


def test_dynamic_config_default_display_rows():
    assert fake_cfg.analytics.max_display_rows == 10000


def test_config_manager_loads_max_display_rows(tmp_path, monkeypatch):
    secret = os.urandom(16).hex()
    yaml = f"""
app:
  title: Test
database:
  name: test.db
security:
  secret_key: {secret}
cache:
  ttl: 1
  jwks_ttl: 1
analytics:
  max_display_rows: 123
"""
    path = tmp_path / "config.yaml"
    path.write_text(yaml)
    envs = {
        "SECRET_KEY": secret,
        "DB_PASSWORD": os.urandom(16).hex(),
        "AUTH0_CLIENT_ID": "x",
        "AUTH0_CLIENT_SECRET": os.urandom(16).hex(),
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
