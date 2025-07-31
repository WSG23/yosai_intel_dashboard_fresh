import asyncio
import base64
import importlib.util
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

otel = types.ModuleType("opentelemetry")
context_mod = types.ModuleType("opentelemetry.context")
otel.context = context_mod
config_mod = types.ModuleType("config")
config_base = types.ModuleType("config.base")
core_protocols = types.ModuleType("core.protocols")
core_protocols.FileProcessorProtocol = object
sys.modules.setdefault("core.protocols", core_protocols)
rabbit_stub = types.ModuleType("services.rabbitmq_client")
rabbit_stub.RabbitMQClient = lambda *a, **k: None
sys.modules.setdefault("services.rabbitmq_client", rabbit_stub)
taskq_stub = types.ModuleType("services.task_queue")
taskq_stub.create_task = lambda *a, **k: "id"
taskq_stub.get_status = lambda *a, **k: {"progress": 0}
sys.modules.setdefault("services.task_queue", taskq_stub)
mem_stub = types.ModuleType("utils.memory_utils")
mem_stub.check_memory_limit = lambda *a, **k: None
sys.modules.setdefault("utils.memory_utils", mem_stub)
fp_stub = types.ModuleType("services.data_processing.file_processor")
fp_stub.UnicodeFileProcessor = types.SimpleNamespace(
    sanitize_dataframe_unicode=lambda df: df,
    read_large_csv=lambda path, **k: pd.read_csv(path, **k),
)
sys.modules.setdefault("services.data_processing.file_processor", fp_stub)
prom = types.ModuleType("prometheus_client")
sys.modules.setdefault("prometheus_client", prom)
config_base.CacheConfig = object
sys.modules.setdefault("config.base", config_base)
dyn = types.SimpleNamespace(
    analytics=types.SimpleNamespace(chunk_size=2, max_memory_mb=1024)
)
config_mod.dynamic_config = dyn
config_mod.DatabaseSettings = lambda *a, **k: None
sys.modules.setdefault("config", config_mod)
sys.modules.setdefault("config.dynamic_config", config_mod)
sys.modules.setdefault("opentelemetry", otel)
sys.modules.setdefault("opentelemetry.context", context_mod)
tracing_stub = types.ModuleType("tracing")
tracing_stub.propagate_context = lambda *a, **k: None
tracing_stub.trace_async_operation = lambda name, coro: coro
sys.modules.setdefault("tracing", tracing_stub)

services_root = Path(__file__).resolve().parents[2] / "services"
services_pkg = types.ModuleType("services")
services_pkg.__path__ = [str(services_root)]
sys.modules.setdefault("services", services_pkg)

upload_pkg = types.ModuleType("services.upload")
upload_pkg.__path__ = [str(services_root / "upload")]
sys.modules.setdefault("services.upload", upload_pkg)
protocols_mod = types.ModuleType("services.upload.protocols")
sys.modules.setdefault("services.upload.protocols", protocols_mod)
data_processing_pkg = types.ModuleType("services.data_processing")
data_processing_pkg.__path__ = [str(services_root / "data_processing")]
sys.modules.setdefault("services.data_processing", data_processing_pkg)

spec = importlib.util.spec_from_file_location(
    "services.task_queue", services_root / "task_queue.py"
)
tq_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(tq_mod)
sys.modules.setdefault("services.task_queue", tq_mod)
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

    proc = AsyncFileProcessor(config=cfg)
    progress = []
    result = asyncio.run(
        proc.process_file(
            data_uri,
            "s.xlsx",
            progress_callback=lambda _f, p: progress.append(p),
        )
    )

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
