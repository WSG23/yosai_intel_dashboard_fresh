from pathlib import Path

from tests.utils.builders import DataFrameBuilder, UploadFileBuilder

from services.data_processing.unified_upload_validator import (
    UnifiedUploadValidator as UploadValidator,
)


def test_validate_file_upload_dataframe():
    df = DataFrameBuilder().add_column("a", [1]).build()
    v = UploadValidator(max_size_mb=1)
    res = v.validate_file_upload(df)
    assert res.valid


def test_validate_file_upload_base64(tmp_path):
    df = DataFrameBuilder().add_column("a", [1]).add_column("b", [2]).build()
    uri = UploadFileBuilder().with_dataframe(df).as_base64()
    v = UploadValidator(max_size_mb=1)
    res = v.validate_file_upload(uri)
    assert res.valid


def test_validate_file_upload_path(tmp_path):
    df = DataFrameBuilder().add_column("a", [1]).add_column("b", [2]).build()
    path = UploadFileBuilder().with_dataframe(df).write_csv(tmp_path / "file.csv")
    v = UploadValidator(max_size_mb=1)
    res = v.validate_file_upload(path)
    assert res.valid
