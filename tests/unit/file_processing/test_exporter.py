from __future__ import annotations

import sys
import types
from pathlib import Path

stub_cfg = types.ModuleType("yosai_intel_dashboard.src.core.config")
stub_cfg.get_max_display_rows = lambda: 100
sys.modules.setdefault("yosai_intel_dashboard.src.core.config", stub_cfg)

import pandas as pd
import pytest

from yosai_intel_dashboard.src.file_processing.exporter import (
    ExportError,
    export_to_parquet,
)


def test_export_parquet(tmp_path: Path):
    df = pd.DataFrame(
        {
            "person_id": ["u"],
            "door_id": ["d"],
            "access_result": ["x"],
            "timestamp": ["2024"],
        }
    )
    path = tmp_path / "out.parquet"
    export_to_parquet(df, str(path), {"a": 1})
    assert path.exists()
    meta = path.with_suffix(".meta.json")
    assert meta.exists()
    out = pd.read_parquet(path)
    assert out.iloc[0]["person_id"] == "u"


def test_export_missing(tmp_path: Path):
    df = pd.DataFrame({"a": [1]})
    with pytest.raises(ExportError):
        export_to_parquet(df, str(tmp_path / "f.parquet"), {})
