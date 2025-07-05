import asyncio
import pandas as pd

from services.upload.async_processor import AsyncUploadProcessor


def test_async_upload_processor_csv_parquet(tmp_path):
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    csv_path = tmp_path / "sample.csv"
    parquet_path = tmp_path / "sample.parquet"

    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)

    proc = AsyncUploadProcessor()

    loaded = asyncio.run(proc.read_csv(csv_path))
    pd.testing.assert_frame_equal(loaded, df)

    preview = asyncio.run(proc.preview_from_parquet(parquet_path, rows=2))
    pd.testing.assert_frame_equal(preview, df.head(2))

    columns_df = asyncio.run(proc.preview_from_parquet(parquet_path, rows=0))
    assert columns_df.empty
    assert list(columns_df.columns) == list(df.columns)
