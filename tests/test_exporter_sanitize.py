from __future__ import annotations

import sys
import types

stub_cfg = types.ModuleType("yosai_intel_dashboard.src.core.config")
stub_cfg.get_max_display_rows = lambda: 100
sys.modules.setdefault("yosai_intel_dashboard.src.core.config", stub_cfg)

import pandas as pd
import pytest

from yosai_intel_dashboard.src.file_processing import exporter


def test_sanitize_path(tmp_path):
    df = pd.DataFrame({"id": [1], "name": ["a"]})
    safe_dir = tmp_path / "exports"
    safe_dir.mkdir()
    path = safe_dir / "out.parquet"
    exporter.EXPORT_ROOT = safe_dir
    exporter.export_to_parquet(df, "out.parquet", {})
    assert path.exists()
    # attempt traversal
    with pytest.raises(exporter.ExportError):
        exporter.export_to_parquet(df, "../evil.parquet", {})
