import time

import pandas as pd
import pytest
import importlib.util
from pathlib import Path
import types
import sys

class InMemoryUploadStore:
    def __init__(self) -> None:
        self.data = {}
    def add_file(self, filename, df):
        self.data[filename] = df
    def get_filenames(self):
        return list(self.data.keys())
    def get_all_data(self):
        return self.data.copy()
    def clear_all(self):
        self.data.clear()
    def load_dataframe(self, filename):
        return self.data.get(filename)
    def get_file_info(self):
        return {k: {"rows": len(v), "columns": len(v.columns)} for k, v in self.data.items()}
    def wait_for_pending_saves(self):
        pass

class FakeFileProcessor:
    async def process_file(self, content, filename, progress_callback=None):
        import base64, pandas as pd, io
        _, data = content.split(",", 1)
        df = pd.read_csv(io.BytesIO(base64.b64decode(data)))
        if progress_callback:
            progress_callback(filename, 100)
        return df

stub_tracing = types.ModuleType("tracing")
stub_tracing.propagate_context = lambda x: x
async def _trace_async_operation(name, tid, coro):
    return await coro
stub_tracing.trace_async_operation = _trace_async_operation
sys.modules.setdefault("tracing", stub_tracing)

sys.modules.setdefault("structlog", types.ModuleType("structlog"))

stub_async = types.ModuleType("services.data_processing.async_file_processor")
stub_async.AsyncFileProcessor = FakeFileProcessor
sys.modules["services.data_processing.async_file_processor"] = stub_async

stub_fh = types.ModuleType("services.data_processing.file_handler")
class DummyFH:
    def __init__(self, max_size_mb=None, **kw):
        pass
    def validate_file_upload(self, file_obj):
        return types.SimpleNamespace(valid=True, message="")
stub_fh.FileHandler = DummyFH
sys.modules["services.data_processing.file_handler"] = stub_fh

stub_store = types.ModuleType("utils.upload_store")
stub_store.UploadedDataStore = InMemoryUploadStore
stub_store.uploaded_data_store = InMemoryUploadStore()
sys.modules["utils.upload_store"] = stub_store
spec = importlib.util.spec_from_file_location(
    "uploader", Path("services/upload/uploader.py")
)
uploader_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(uploader_mod)
Uploader = uploader_mod.Uploader
from services.data_processing.file_handler import FileHandler
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder


def _wait_done(uploader: Uploader, job_id: str, timeout: float = 5.0):
    start = time.time()
    while time.time() - start < timeout:
        status = uploader.get_job_status(job_id)
        if status.get("done"):
            return status
        time.sleep(0.01)
    pytest.fail("job did not finish")


def test_validate_and_store_file_success():
    df = DataFrameBuilder().add_column("a", [1, 2]).build()
    content = UploadFileBuilder().with_dataframe(df).as_base64()

    store = InMemoryUploadStore()
    uploader = Uploader(store, FileHandler(max_size_mb=1), FakeFileProcessor())

    job_id = uploader.validate_and_store_file(content, "sample.csv")
    status = _wait_done(uploader, job_id)
    assert status["result"]["rows"] == len(df)
    assert "sample.csv" in store.get_filenames()


def test_validate_and_store_file_validation_error():
    df = DataFrameBuilder().add_column("a", [1]).build()
    content = UploadFileBuilder().with_dataframe(df).with_filename("bad.exe").as_base64()

    store = InMemoryUploadStore()
    class BadHandler(DummyFH):
        def validate_file_upload(self, file_obj):
            return types.SimpleNamespace(valid=False, message="bad")

    uploader = Uploader(store, BadHandler(), FakeFileProcessor())

    with pytest.raises(ValueError):
        uploader.validate_and_store_file(content, "bad.exe")
