import pandas as pd

from yosai_intel_dashboard.src.services.upload.file_processor_service import FileProcessor
from tests.unit.fakes import (
    FakeFileProcessor,
    FakeUploadDataService,
    FakeUploadStore,
)
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder


def test_file_processor_roundtrip(async_runner):
    df = DataFrameBuilder().add_column("a", [1]).build()
    content = UploadFileBuilder().with_dataframe(df).as_base64()
    store = FakeUploadStore()
    data = FakeUploadDataService(store)
    processor = FileProcessor(store, FakeFileProcessor(), data)
    res = async_runner(processor.process_files({"x.csv": [content]}))
    info = res["x.csv"]
    assert info["rows"] == len(df)
    assert "df" in info
    assert not info.get("error")
    assert "x.csv" in store.get_filenames()
