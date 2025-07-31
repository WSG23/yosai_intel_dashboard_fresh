import pandas as pd
import pytest

from yosai_intel_dashboard.src.file_processing import exporter


def test_sanitize_path(tmp_path):
    df = pd.DataFrame({"id": [1], "name": ["a"]})
    safe_dir = tmp_path / "exports"
    safe_dir.mkdir()
    path = safe_dir / "out.csv"
    exporter.EXPORT_ROOT = safe_dir
    exporter.export_to_csv(df, "out.csv", {})
    assert path.exists()
    # attempt traversal
    with pytest.raises(exporter.ExportError):
        exporter.export_to_csv(df, "../evil.csv", {})
