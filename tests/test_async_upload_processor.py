import asyncio

from yosai_intel_dashboard.src.services.upload.async_processor import AsyncUploadProcessor
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder


def test_async_upload_processor_csv_parquet(tmp_path, async_runner):
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    csv_path = tmp_path / "sample.csv"

    parquet_path = tmp_path / "sample.parquet"

    proc = AsyncUploadProcessor()

    loaded = async_runner(proc.read_csv(csv_path))
    pd.testing.assert_frame_equal(loaded, df)

    preview = async_runner(proc.preview_from_parquet(parquet_path, rows=2))
    pd.testing.assert_frame_equal(preview, df.head(2))

    columns_df = async_runner(proc.preview_from_parquet(parquet_path, rows=0))
    assert columns_df.empty
    assert list(columns_df.columns) == list(df.columns)
