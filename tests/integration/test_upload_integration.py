import asyncio
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# provide minimal stubs for config dependencies
import types
conn_mod = types.ModuleType("config.connection_retry")
class RetryConfig:
    def __init__(self, max_attempts=3, base_delay=0.2, jitter=False):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.jitter = jitter
class ConnectionRetryManager:
    def __init__(self, cfg=None):
        self.cfg = cfg or RetryConfig()
    def run_with_retry(self, func):
        return func()
conn_mod.RetryConfig = RetryConfig
conn_mod.ConnectionRetryManager = ConnectionRetryManager
sys.modules["config.connection_retry"] = conn_mod
spec_queue = importlib.util.spec_from_file_location(
    "upload_queue_manager", ROOT / "services" / "upload" / "upload_queue_manager.py"
)
queue_mod = importlib.util.module_from_spec(spec_queue)

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

sys.modules["upload_queue_manager"] = queue_mod
spec_queue.loader.exec_module(queue_mod)  # type: ignore
UploadQueueManager = queue_mod.UploadQueueManager

spec_chunk = importlib.util.spec_from_file_location(
    "chunked_upload_manager", ROOT / "services" / "upload" / "chunked_upload_manager.py"
)
chunk_mod = importlib.util.module_from_spec(spec_chunk)
sys.modules["chunked_upload_manager"] = chunk_mod
spec_chunk.loader.exec_module(chunk_mod)  # type: ignore
ChunkedUploadManager = chunk_mod.ChunkedUploadManager



def test_resumable_upload_and_error_callback(tmp_path, monkeypatch, fake_upload_storage):
    data_file = tmp_path / "sample.csv"
    df = pd.DataFrame({"a": range(15)})
    df.to_csv(data_file, index=False)

    store = fake_upload_storage
    cmgr = ChunkedUploadManager(store, metadata_dir=tmp_path / "meta", initial_chunk_size=5)
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
