import asyncio
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from config.connection_retry import ConnectionRetryManager, RetryConfig
from yosai_intel_dashboard.src.services.upload.chunked_upload_manager import ChunkedUploadManager
from yosai_intel_dashboard.src.services.upload.upload_queue_manager import UploadQueueManager
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder


@pytest.fixture
def fast_retry_manager_cls():
    class FastRetryManager(ConnectionRetryManager):
        def __init__(self, cfg=None):
            super().__init__(
                cfg or RetryConfig(max_attempts=3, base_delay=0, jitter=False)
            )

        def run_with_retry(self, func):  # type: ignore[override]
            return func()

    return FastRetryManager


class CallbackEvent:
    ANALYSIS_ERROR = "ANALYSIS_ERROR"


class CallbackContext:
    def __init__(self, event_type, source_id, timestamp, data=None):
        self.event_type = event_type
        self.source_id = source_id
        self.timestamp = timestamp
        self.data = data or {}


class CallbackManager:
    def __init__(self):
        self.callbacks = []

    def register_callback(self, event, func, priority=50):
        self.callbacks.append(func)

    def trigger(self, event, ctx):
        for cb in list(self.callbacks):
            cb(ctx)


def test_resumable_upload_and_error_callback(
    tmp_path, monkeypatch, fake_upload_storage, fast_retry_manager_cls
):
    data_file = tmp_path / "sample.csv"
    df = DataFrameBuilder().add_column("a", range(15)).build()
    UploadFileBuilder().with_dataframe(df).write_csv(data_file)

    store = fake_upload_storage
    cmgr = ChunkedUploadManager(
        store,
        metadata_dir=tmp_path / "meta",
        initial_chunk_size=5,
        retry_manager_cls=fast_retry_manager_cls,
    )
    queue = UploadQueueManager(max_concurrent=1)
    queue.add_files([data_file])

    cb_manager = CallbackManager()
    errors: list[str] = []
    cb_manager.register_callback(
        CallbackEvent.ANALYSIS_ERROR,
        lambda ctx: errors.append(ctx.data.get("err")),
    )

    call_count = 0
    original_add = store.add_file

    def flaky(name: str, chunk_df: pd.DataFrame):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("fail")
        original_add(name, chunk_df)

    monkeypatch.setattr(store, "add_file", flaky)

    async def handler(path: Path):
        try:
            cmgr.upload_file(path)
        except Exception as exc:  # first attempt fails
            cb_manager.trigger(
                CallbackEvent.ANALYSIS_ERROR,
                CallbackContext(
                    CallbackEvent.ANALYSIS_ERROR,
                    "uploader",
                    datetime.now(),
                    {"err": str(exc)},
                ),
            )
            raise

    async def _run():
        results = []
        for _ in range(3):
            results.extend(await queue.process_queue(handler))
            if results:
                break
            await asyncio.sleep(0.01)
        return results

    results = asyncio.run(_run())

    assert results and isinstance(results[0][1], Exception)
    assert errors  # callback captured error

    monkeypatch.setattr(store, "add_file", original_add)
    cmgr.resume_upload(data_file)
    store.wait_for_pending_saves()
    assert cmgr.get_upload_progress("sample.csv") == pytest.approx(1.0)
    saved = store.load_dataframe("sample.csv")
    pd.testing.assert_frame_equal(saved, df)
