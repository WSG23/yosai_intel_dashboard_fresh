import asyncio
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from yosai_intel_dashboard.src.infrastructure.config.connection_retry import ConnectionRetryManager, RetryConfig
import importlib.util
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder
from pathlib import Path as _Path
import importlib.util as _importlib
import sys as _sys
import types as _types

MODULE_PATH = (
    _Path(__file__).resolve().parents[2]
    / "yosai_intel_dashboard"
    / "src"
    / "file_processing"
    / "data_processor.py"
)

truly_stub = _types.SimpleNamespace(TrulyUnifiedCallbacks=object)
cb_events_stub = _types.SimpleNamespace(CallbackEvent=_types.SimpleNamespace(SYSTEM_WARNING=1, SYSTEM_ERROR=2))
container_stub = _types.ModuleType("core.container")
container_stub.get_unicode_processor = lambda: _types.SimpleNamespace(sanitize_dataframe=lambda df: df)

_sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks",
    truly_stub,
)
format_stub = _types.ModuleType("file_processing.format_detector")
class FormatDetector:
    def __init__(self, *a, **k): ...
    def detect_and_load(self, path, hint=None):
        return pd.read_csv(path), {}
class UnsupportedFormatError(Exception):
    pass
format_stub.FormatDetector = FormatDetector
format_stub.UnsupportedFormatError = UnsupportedFormatError
_sys.modules.setdefault("file_processing.format_detector", format_stub)

readers_stub = _types.ModuleType("file_processing.readers")
for _name in ["CSVReader", "ExcelReader", "JSONReader", "FWFReader", "ArchiveReader"]:
    setattr(readers_stub, _name, type(_name, (), {}))
_sys.modules.setdefault("file_processing.readers", readers_stub)
_sys.modules.setdefault("core.callback_events", cb_events_stub)
_sys.modules.setdefault("core.container", container_stub)
pkg = _types.ModuleType("file_processing")
pkg.__path__ = [str(MODULE_PATH.parent)]
_sys.modules.setdefault("file_processing", pkg)
spec = _importlib.spec_from_file_location("file_processing.data_processor", MODULE_PATH)
dp_mod = _importlib.module_from_spec(spec)
_sys.modules["file_processing.data_processor"] = dp_mod
assert spec.loader is not None
spec.loader.exec_module(dp_mod)
DataProcessor = dp_mod.DataProcessor


def _load_upload_queue_manager():
    path = Path(__file__).resolve().parents[2] / "services" / "upload" / "upload_queue_manager.py"
    spec = importlib.util.spec_from_file_location("upload_queue_manager", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.UploadQueueManager


def _load_chunked_manager():
    path = Path(__file__).resolve().parents[2] / "services" / "upload" / "chunked_upload_manager.py"
    spec = importlib.util.spec_from_file_location("chunked_upload_manager", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.ChunkedUploadManager


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


class TrulyUnifiedCallbacks:
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
    ChunkedUploadManager = _load_chunked_manager()
    cmgr = ChunkedUploadManager(
        store,
        metadata_dir=tmp_path / "meta",
        initial_chunk_size=5,
        retry_manager_cls=fast_retry_manager_cls,
    )
    UploadQueueManager = _load_upload_queue_manager()
    queue = UploadQueueManager(max_concurrent=1)
    queue.add_files([data_file])

    cb_manager = TrulyUnifiedCallbacks()
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


def test_upload_and_process_csv(tmp_path, monkeypatch, fake_upload_storage):
    csv_path = tmp_path / "data.csv"
    df = (
        DataFrameBuilder()
        .add_column("timestamp", ["2024-05-05 12:00:00"])
        .add_column("person_id", ["P1"])
        .add_column("badge_id", ["B1"])
        .add_column("device_name", ["Entrance"])
        .add_column("door_id", ["D1"])
        .add_column("access_result", ["granted"])
        .build()
    )
    UploadFileBuilder().with_dataframe(df).write_csv(csv_path)

    store = fake_upload_storage
    ChunkedUploadManager = _load_chunked_manager()
    mgr = ChunkedUploadManager(store, metadata_dir=tmp_path / "meta", initial_chunk_size=2)
    mgr.upload_file(csv_path)
    store.wait_for_pending_saves()
    assert mgr.get_upload_progress("data.csv") == pytest.approx(1.0)

    monkeypatch.setattr(DataProcessor, "_enrich_devices", lambda self, d: d)
    monkeypatch.setattr(DataProcessor, "_schema_validate", lambda self, d: d)
    monkeypatch.setattr(
        DataProcessor,
        "_infer_boolean_flags",
        lambda self, d: d.assign(is_entry=False, is_exit=False),
    )
    processor = DataProcessor()
    processed = processor.process(str(csv_path))
    store.add_file("data.csv", processed)

    saved = store.load_dataframe("data.csv")
    pd.testing.assert_frame_equal(saved.reset_index(drop=True), processed.reset_index(drop=True))
