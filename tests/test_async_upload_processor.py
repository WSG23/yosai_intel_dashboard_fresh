import asyncio

from tests.utils.builders import DataFrameBuilder, UploadFileBuilder

from services.upload.async_processor import AsyncUploadProcessor


def test_async_upload_processor_csv_parquet(tmp_path):
    df = (
        DataFrameBuilder()
        .add_column("a", [1, 2, 3])
        .add_column("b", ["x", "y", "z"])
        .build()
    )
    csv_path = UploadFileBuilder().with_dataframe(df).write_csv(tmp_path / "sample.csv")
    df.to_parquet(tmp_path / "sample.parquet", index=False)
    parquet_path = tmp_path / "sample.parquet"

    proc = AsyncUploadProcessor()

    loaded = asyncio.run(proc.read_csv(csv_path))
    pd.testing.assert_frame_equal(loaded, df)

    preview = asyncio.run(proc.preview_from_parquet(parquet_path, rows=2))
    pd.testing.assert_frame_equal(preview, df.head(2))

    columns_df = asyncio.run(proc.preview_from_parquet(parquet_path, rows=0))
    assert columns_df.empty
    assert list(columns_df.columns) == list(df.columns)
