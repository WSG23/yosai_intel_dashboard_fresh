from pathlib import Path

import pandas as pd

from yosai_intel_dashboard.src.file_processing.data_processor import DataProcessor


def test_load_file_updates_metadata(tmp_path: Path):
    df = pd.DataFrame({"a": [1]})
    path = tmp_path / "f.csv"
    df.to_csv(path, index=False)
    processor = DataProcessor()
    out = processor.load_file(str(path))
    assert "last_ingest" in processor.pipeline_metadata
    assert out.equals(df)
