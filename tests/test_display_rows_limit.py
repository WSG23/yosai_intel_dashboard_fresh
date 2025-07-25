import pandas as pd

from config import get_config
from yosai_intel_dashboard.src.services.data_processing.file_processor import create_file_preview


def test_create_file_preview_respects_limit(monkeypatch):
    monkeypatch.setattr(get_config().config.analytics, "max_display_rows", 5)
    df = pd.DataFrame({"a": range(20)})
    preview = create_file_preview(df)
    assert len(preview["preview_data"]) == 5


def test_large_data_not_truncated(monkeypatch):
    monkeypatch.setattr(get_config().config.analytics, "max_display_rows", 10000)
    df = pd.DataFrame({"a": range(200)})
    preview = create_file_preview(df)
    assert preview["total_rows"] == 200
