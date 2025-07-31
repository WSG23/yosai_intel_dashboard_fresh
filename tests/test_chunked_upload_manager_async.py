import asyncio

import pandas as pd
import pytest

from yosai_intel_dashboard.src.services.upload.chunked_upload_manager_async import ChunkedUploadManager
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder
from utils.upload_store import UploadedDataStore


def _create_csv(path, rows=30):
    df = DataFrameBuilder().add_column("a", range(rows)).build()
    UploadFileBuilder().with_dataframe(df).write_csv(path)
    return df


def test_async_chunked_upload_manager_basic(tmp_path, async_runner):
    data_file = tmp_path / "sample.csv"
    df = _create_csv(data_file, rows=25)
    store = UploadedDataStore(storage_dir=tmp_path / "store")
    mgr = ChunkedUploadManager(
        store, metadata_dir=tmp_path / "meta", initial_chunk_size=10
    )

    async_runner(mgr.upload_file(data_file))
    store.wait_for_pending_saves()

    progress = async_runner(mgr.get_upload_progress("sample.csv"))
    assert progress == pytest.approx(1.0)
    saved = store.load_dataframe("sample.csv")
    pd.testing.assert_frame_equal(saved, df)


def test_async_chunked_upload_manager_resume(tmp_path, monkeypatch, async_runner):
    data_file = tmp_path / "resume.csv"
    df = _create_csv(data_file, rows=30)
    store = UploadedDataStore(storage_dir=tmp_path / "store")
    mgr = ChunkedUploadManager(
        store, metadata_dir=tmp_path / "meta", initial_chunk_size=10
    )

    call_count = 0
    original_add_file = store.add_file

    def fail_second(name, chunk_df):
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise RuntimeError("fail")
        original_add_file(name, chunk_df)

    monkeypatch.setattr(store, "add_file", fail_second)
    from config.connection_retry import ConnectionRetryExhausted

    with pytest.raises(ConnectionRetryExhausted):
        async_runner(mgr.upload_file(data_file))

    progress = async_runner(mgr.get_upload_progress("resume.csv"))
    assert 0 < progress < 1

    monkeypatch.setattr(store, "add_file", original_add_file)
    async_runner(mgr.resume_upload(data_file))
    store.wait_for_pending_saves()

    progress = async_runner(mgr.get_upload_progress("resume.csv"))
    assert progress == pytest.approx(1.0)
    saved = store.load_dataframe("resume.csv")
    pd.testing.assert_frame_equal(saved, df)


def test_async_chunked_upload_manager_retry(tmp_path, monkeypatch, async_runner):
    data_file = tmp_path / "retry.csv"
    df = _create_csv(data_file, rows=10)
    store = UploadedDataStore(storage_dir=tmp_path / "store")
    mgr = ChunkedUploadManager(
        store, metadata_dir=tmp_path / "meta", initial_chunk_size=5
    )

    call_count = 0
    original_add_file = store.add_file

    def fail_once(name, chunk_df):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RuntimeError("boom")
        original_add_file(name, chunk_df)

    monkeypatch.setattr(store, "add_file", fail_once)
    async_runner(mgr.upload_file(data_file))
    store.wait_for_pending_saves()

    progress = async_runner(mgr.get_upload_progress("retry.csv"))
    assert progress == pytest.approx(1.0)
    saved = store.load_dataframe("retry.csv")
    pd.testing.assert_frame_equal(saved, df)
