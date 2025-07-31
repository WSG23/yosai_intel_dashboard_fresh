from __future__ import annotations

import pandas as pd

from config.dynamic_config import dynamic_config
from file_processing import create_file_preview


def test_create_file_preview_respects_limit(monkeypatch):
    monkeypatch.setattr(dynamic_config.analytics, "max_display_rows", 5)
    df = pd.DataFrame({"a": range(20)})
    preview = create_file_preview(df)
    assert len(preview["preview_data"]) == 5


def test_large_data_not_truncated(monkeypatch):
    monkeypatch.setattr(dynamic_config.analytics, "max_display_rows", 10000)
    df = pd.DataFrame({"a": range(200)})
    preview = create_file_preview(df)
    assert preview["total_rows"] == 200
