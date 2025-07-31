import json
import os
from pathlib import Path

import pandas as pd
import pytest

from yosai_intel_dashboard.src.file_processing.exporter import (
    ExportError,
    export_to_csv,
    export_to_json,
)


def test_export_csv(tmp_path: Path):
    df = pd.DataFrame(
        {
            "person_id": ["u"],
            "door_id": ["d"],
            "access_result": ["x"],
            "timestamp": ["2024"],
        }
    )
    path = tmp_path / "out.csv"
    export_to_csv(df, str(path), {})
    assert path.exists()
    meta = path.with_suffix(".meta.json")
    assert meta.exists()
    content = path.read_bytes()
    assert content.startswith(b"\xef\xbb\xbf")


def test_export_json(tmp_path: Path):
    df = pd.DataFrame(
        {
            "person_id": ["u"],
            "door_id": ["d"],
            "access_result": ["x"],
            "timestamp": ["2024"],
        }
    )
    path = tmp_path / "out.json"
    export_to_json(df, str(path), {"a": 1})
    assert path.exists() and path.with_suffix(".meta.json").exists()
    data = json.loads(path.read_text())
    assert data[0]["person_id"] == "u"


def test_export_missing(tmp_path: Path):
    df = pd.DataFrame({"a": [1]})
    with pytest.raises(ExportError):
        export_to_csv(df, str(tmp_path / "f.csv"), {})
