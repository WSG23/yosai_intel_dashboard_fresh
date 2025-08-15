import asyncio
import importlib
import importlib.util
import sys
import time
import types
from pathlib import Path

import pandas as pd
import pytest

from tests.utils.builders import DataFrameBuilder, UploadFileBuilder
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

services_root = Path(__file__).resolve().parents[1] / "services"
services_pkg = types.ModuleType("services")
services_pkg.__path__ = [str(services_root)]
safe_import('services', services_pkg)

upload_pkg = types.ModuleType("services.upload")
upload_pkg.__path__ = [str(services_root / "upload")]
safe_import('services.upload', upload_pkg)

spec = importlib.util.spec_from_file_location(
    "services.upload.protocols", services_root / "upload" / "protocols.py"
)
protocols_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(protocols_mod)
safe_import('services.upload.protocols', protocols_mod)

data_processing_pkg = types.ModuleType("services.data_processing")
data_processing_pkg.__path__ = [str(services_root / "data_processing")]
safe_import('services.data_processing', data_processing_pkg)

spec = importlib.util.spec_from_file_location(
    "services.task_queue", services_root / "task_queue.py"
)
task_queue_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(task_queue_module)
safe_import('services.task_queue', task_queue_module)
clear_task = task_queue_module.clear_task
create_task = task_queue_module.create_task
get_status = task_queue_module.get_status

spec = importlib.util.spec_from_file_location(
    "services.data_processing.async_file_processor",
    services_root / "data_processing" / "async_file_processor.py",
)
async_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(async_module)
AsyncFileProcessor = async_module.AsyncFileProcessor
cfg = types.SimpleNamespace(
    analytics=types.SimpleNamespace(chunk_size=2, max_memory_mb=1024)
)
from yosai_intel_dashboard.src.infrastructure.callbacks import (
    CallbackType,
    UnifiedCallbackRegistry,
)


def test_async_file_processor_progress(tmp_path):
    df = pd.DataFrame({"a": range(5)})
    path = tmp_path / "data.csv"
    df.to_csv(path, index=False)

    registry = UnifiedCallbackRegistry()
    processor = AsyncFileProcessor(
        chunk_size=2, config=cfg, callback_registry=registry
    )

    async def job(progress):
        registry.register_callback(
            CallbackType.PROGRESS, progress, component_id=str(path)
        )
        return await processor.load_csv(path, component_id=str(path))

    tid = create_task(job)
    last = 0
    while True:
        status = get_status(tid)
        cur = status["progress"]
        assert cur >= last
        last = cur
        if status.get("done"):
            break
        time.sleep(0.01)

    result = status["result"]
    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(df)
    assert last == 100
    clear_task(tid)


def test_read_uploaded_file_outside_loop(tmp_path):
    df = DataFrameBuilder().add_column("a", range(2)).build()
    content = UploadFileBuilder().with_dataframe(df).as_base64()

    processor = AsyncFileProcessor(config=cfg)
    loaded, err = asyncio.run(processor.read_uploaded_file(content, "sample.csv"))

    assert err == ""
    assert len(loaded) == len(df)


@pytest.mark.asyncio
async def test_read_uploaded_file_inside_loop(tmp_path):
    df = DataFrameBuilder().add_column("a", range(2)).build()
    content = UploadFileBuilder().with_dataframe(df).as_base64()

    processor = AsyncFileProcessor(config=cfg)
    loaded, err = await processor.read_uploaded_file(content, "sample.csv")

    assert err == ""
    assert len(loaded) == len(df)


def test_process_file_async(tmp_path):
    df = DataFrameBuilder().add_column("a", range(3)).build()
    content = UploadFileBuilder().with_dataframe(df).as_base64()

    processor = AsyncFileProcessor(config=cfg)
    job_id = processor.process_file_async(content, "sample.csv")

    last = 0
    while True:
        status = processor.get_job_status(job_id)
        cur = status["progress"]
        assert cur >= last
        last = cur
        if status.get("done"):
            break
        time.sleep(0.01)

    result = status["result"]
    assert result["rows"] == len(df)
    clear_task(job_id)
