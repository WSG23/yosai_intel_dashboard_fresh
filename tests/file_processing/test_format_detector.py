from pathlib import Path

import pandas as pd
import pytest

from yosai_intel_dashboard.src.file_processing.format_detector import (
    FormatDetector,
    UnsupportedFormatError,
)
from yosai_intel_dashboard.src.file_processing.readers import (
    ArchiveReader,
    CSVReader,
    ExcelReader,
    FWFReader,
    JSONReader,
)


@pytest.fixture()
def detector():
    return FormatDetector(
        [CSVReader(), JSONReader(), ExcelReader(), FWFReader(), ArchiveReader()]
    )


def test_detect_csv(tmp_path: Path, detector):
    df = pd.DataFrame({"a": [1, 2]})
    csv_path = tmp_path / "test.csv"
    df.to_csv(csv_path, index=False)
    out, meta = detector.detect_and_load(str(csv_path))
    assert list(out.columns) == ["a"]
    assert meta["detected_type"] == "csv"


def test_detect_json(tmp_path: Path, detector):
    df = pd.DataFrame({"b": [1]})
    json_path = tmp_path / "test.json"
    df.to_json(json_path, orient="records")
    out, meta = detector.detect_and_load(str(json_path))
    assert "b" in out.columns
    assert meta["detected_type"] == "json"


def test_detect_excel(tmp_path: Path, detector):
    df = pd.DataFrame({"c": [1]})
    xl_path = tmp_path / "t.xlsx"
    df.to_excel(xl_path, index=False)
    out, meta = detector.detect_and_load(str(xl_path))
    assert "c" in out.columns
    assert meta["detected_type"] == "excel"


def test_unsupported(tmp_path: Path, detector):
    txt = tmp_path / "t.txt"
    txt.write_text("hello")
    with pytest.raises(UnsupportedFormatError):
        detector.detect_and_load(str(txt))
