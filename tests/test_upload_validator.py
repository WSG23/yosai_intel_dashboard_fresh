from __future__ import annotations

from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import dynamic_config
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder
from validation.upload_utils import decode_and_validate_upload


def test_decode_and_validate_upload_valid():
    df = DataFrameBuilder().add_column("a", [1]).build()
    uri = UploadFileBuilder().with_dataframe(df).as_base64()
    result = decode_and_validate_upload(uri, "data.csv")
    assert result["valid"]
    assert result["decoded"]


def test_decode_and_validate_upload_invalid_data_uri():
    result = decode_and_validate_upload("not_base64", "bad.csv")
    assert not result["valid"]


def test_decode_and_validate_upload_size_limit(monkeypatch):
    df = DataFrameBuilder().add_column("a", [1]).build()
    uri = UploadFileBuilder().with_dataframe(df).as_base64()
    monkeypatch.setattr(dynamic_config.security, "max_upload_mb", 0)
    result = decode_and_validate_upload(uri, "data.csv")
    assert not result["valid"]
