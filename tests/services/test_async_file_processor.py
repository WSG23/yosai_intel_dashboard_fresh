import asyncio
import base64
import importlib.util
import sys
import types
from pathlib import Path

import pandas as pd
import pytest
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

otel = types.ModuleType("opentelemetry")
context_mod = types.ModuleType("opentelemetry.context")
otel.context = context_mod
config_mod = types.ModuleType("config")
config_base = types.ModuleType("config.base")
core_protocols = types.ModuleType("core.protocols")
core_protocols.FileProcessorProtocol = object
safe_import('core.protocols', core_protocols)
rabbit_stub = types.ModuleType("services.rabbitmq_client")
rabbit_stub.RabbitMQClient = lambda *a, **k: None
safe_import('services.rabbitmq_client', rabbit_stub)
taskq_stub = types.ModuleType("services.task_queue")
taskq_stub.create_task = lambda *a, **k: "id"
taskq_stub.get_status = lambda *a, **k: {"progress": 0}
safe_import('services.task_queue', taskq_stub)
mem_stub = types.ModuleType("utils.memory_utils")
mem_stub.check_memory_limit = lambda *a, **k: None
safe_import('utils.memory_utils', mem_stub)
fp_stub = types.ModuleType("services.data_processing.file_processor")
fp_stub.UnicodeFileProcessor = types.SimpleNamespace(
    sanitize_dataframe_unicode=lambda df: df,
    read_large_csv=lambda path, **k: pd.read_csv(path, **k),
)
safe_import('services.data_processing.file_processor', fp_stub)
prom = types.ModuleType("prometheus_client")
safe_import('prometheus_client', prom)
config_base.CacheConfig = object
safe_import('config.base', config_base)
dyn = types.SimpleNamespace(
    analytics=types.SimpleNamespace(chunk_size=2, max_memory_mb=1024)
)
config_mod.dynamic_config = dyn
config_mod.DatabaseSettings = lambda *a, **k: None
safe_import('config', config_mod)
safe_import('config.dynamic_config', config_mod)
safe_import('opentelemetry', otel)
safe_import('opentelemetry.context', context_mod)
tracing_stub = types.ModuleType("tracing")
tracing_stub.propagate_context = lambda *a, **k: None
tracing_stub.trace_async_operation = lambda name, coro: coro
safe_import('tracing', tracing_stub)

services_root = Path(__file__).resolve().parents[2] / "services"
services_pkg = types.ModuleType("services")
services_pkg.__path__ = [str(services_root)]
safe_import('services', services_pkg)

upload_pkg = types.ModuleType("services.upload")
upload_pkg.__path__ = [str(services_root / "upload")]
safe_import('services.upload', upload_pkg)
protocols_mod = types.ModuleType("services.upload.protocols")
safe_import('services.upload.protocols', protocols_mod)
data_processing_pkg = types.ModuleType("services.data_processing")
data_processing_pkg.__path__ = [str(services_root / "data_processing")]
safe_import('services.data_processing', data_processing_pkg)

spec = importlib.util.spec_from_file_location(
    "services.task_queue", services_root / "task_queue.py"
)
tq_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(tq_mod)
safe_import('services.task_queue', tq_mod)
clear_task = tq_mod.clear_task

spec = importlib.util.spec_from_file_location(
    "services.data_processing.async_file_processor",
    services_root / "data_processing" / "async_file_processor.py",
)
async_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(async_mod)
AsyncFileProcessor = async_mod.AsyncFileProcessor
cfg = dyn
from yosai_intel_dashboard.src.infrastructure.callbacks import (
    CallbackType,
    UnifiedCallbackRegistry,
)


def test_read_csv_chunks_and_load(tmp_path: Path):
    df = pd.DataFrame({"a": [1, 2, 3], "b": list("xyz")})
    csv_path = tmp_path / "sample.csv"
    df.to_csv(csv_path, index=False)

    proc = AsyncFileProcessor(chunk_size=2, config=cfg)

    async def gather():
        chunks = []
        async for chunk in proc.read_csv_chunks(csv_path):
            chunks.append(chunk)
        return pd.concat(chunks, ignore_index=True)

    loaded_chunks = asyncio.run(gather())
    assert loaded_chunks.equals(df)

    loaded = asyncio.run(proc.load_csv(csv_path))
    assert loaded.equals(df)


def test_process_excel_file(tmp_path: Path):
    df = pd.DataFrame({"a": [5, 6], "b": ["m", "n"]})
    xl_path = tmp_path / "s.xlsx"
    df.to_excel(xl_path, index=False)
    contents = base64.b64encode(xl_path.read_bytes()).decode()
    data_uri = (
        "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,"
        + contents
    )

    registry = UnifiedCallbackRegistry()
    proc = AsyncFileProcessor(config=cfg, callback_registry=registry)
    progress = []
    registry.register_callback(
        CallbackType.PROGRESS, lambda p: progress.append(p), component_id="s.xlsx"
    )
    result = asyncio.run(proc.process_file(data_uri, "s.xlsx"))

    assert result.equals(df)
    assert progress and progress[-1] == 100
    clear_task.cache_clear() if hasattr(clear_task, "cache_clear") else None


def test_read_uploaded_file_csv(tmp_path: Path):
    df = pd.DataFrame({"x": [1, 2], "y": ["a", "b"]})
    csv_path = tmp_path / "t.csv"
    df.to_csv(csv_path, index=False)
    contents = base64.b64encode(csv_path.read_bytes()).decode()
    data_uri = "data:text/csv;base64," + contents

    proc = AsyncFileProcessor(config=cfg)
    loaded, _ = asyncio.run(proc.read_uploaded_file(data_uri, "t.csv"))
    assert loaded.equals(df)
