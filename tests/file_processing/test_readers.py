from pathlib import Path

import pandas as pd
import pytest

from yosai_intel_dashboard.src.file_processing.readers import (
    BaseReader,
    CSVReader,
    ExcelReader,
    JSONReader,
)
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
    TrulyUnifiedCallbacks,
)


@pytest.mark.parametrize(
    "reader,ext,writer",
    [
        (CSVReader(), ".csv", lambda df, p: df.to_csv(p, index=False)),
        (JSONReader(), ".json", lambda df, p: df.to_json(p, orient="records")),
        (ExcelReader(), ".xlsx", lambda df, p: df.to_excel(p, index=False)),
    ],
)
def test_reader_success(tmp_path: Path, reader, ext, writer):
    df = pd.DataFrame({"a": [1, 2]})
    path = tmp_path / f"t{ext}"
    writer(df, path)
    out = reader.read(str(path))
    assert len(out) == len(df)


def test_cannot_parse(tmp_path: Path):
    path = tmp_path / "bad.csv"
    path.write_text("")
    with pytest.raises(CSVReader.CannotParse):
        CSVReader().read(str(path))


def test_readers_provide_unified_callbacks():
    for cls in (CSVReader, JSONReader, ExcelReader):
        reader = cls()
        assert isinstance(reader, BaseReader)
        assert isinstance(reader.unified_callbacks, TrulyUnifiedCallbacks)
