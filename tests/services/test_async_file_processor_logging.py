from __future__ import annotations

import asyncio
import base64
import concurrent.futures
import importlib.util
import logging
import os
import sys
import types
import uuid
from pathlib import Path

import pandas as pd
import pytest

from yosai_intel_dashboard.src.core.imports.resolver import safe_import
from yosai_intel_dashboard.src.services.data_processing.core.exceptions import (
    FileProcessingError,
)

# Setup minimal stubs as in existing async processor tests
otel = types.ModuleType("opentelemetry")
context_mod = types.ModuleType("opentelemetry.context")
otel.context = context_mod
config_mod = types.ModuleType("config")
config_base = types.ModuleType("config.base")
core_protocols = types.ModuleType("core.protocols")
core_protocols.FileProcessorProtocol = object
safe_import("core.protocols", core_protocols)
rabbit_stub = types.ModuleType("services.kafka_client")
rabbit_stub.KafkaClient = lambda *a, **k: None
safe_import("services.kafka_client", rabbit_stub)
taskq_stub = types.ModuleType("services.task_queue")
taskq_stub.create_task = lambda *a, **k: "id"
taskq_stub.get_status = lambda *a, **k: {"progress": 0}
safe_import("services.task_queue", taskq_stub)
mem_stub = types.ModuleType("utils.memory_utils")
mem_stub.check_memory_limit = lambda *a, **k: None
safe_import("utils.memory_utils", mem_stub)
utils_pkg = types.ModuleType("yosai_intel_dashboard.src.utils")
sys.modules["yosai_intel_dashboard.src.utils"] = utils_pkg
sys.modules["yosai_intel_dashboard.src.utils.memory_utils"] = mem_stub
hashing_stub = types.ModuleType("yosai_intel_dashboard.src.utils.hashing")
hashing_stub.hash_dataframe = lambda df: ""
sys.modules["yosai_intel_dashboard.src.utils.hashing"] = hashing_stub
utils_pkg.hashing = hashing_stub
fp_stub = types.ModuleType("services.data_processing.file_processor")
fp_stub.UnicodeFileProcessor = types.SimpleNamespace(
    sanitize_dataframe_unicode=lambda df: df,
    read_large_csv=lambda path, **k: pd.read_csv(path, **k),
)
safe_import("services.data_processing.file_processor", fp_stub)
config_base.CacheConfig = object
safe_import("config.base", config_base)
dyn = types.SimpleNamespace(
    analytics=types.SimpleNamespace(chunk_size=2, max_memory_mb=1024),
)
config_mod.dynamic_config = dyn
config_mod.DatabaseSettings = lambda *a, **k: None
safe_import("config", config_mod)
safe_import("config.dynamic_config", config_mod)
safe_import("opentelemetry", otel)
safe_import("opentelemetry.context", context_mod)
tracing_stub = types.ModuleType("tracing")
tracing_stub.propagate_context = lambda *a, **k: None
tracing_stub.trace_async_operation = lambda name, coro: coro
safe_import("tracing", tracing_stub)

concurrent.futures.ProcessPoolExecutor = lambda *a, **k: types.SimpleNamespace()

services_root = (
    Path(__file__).resolve().parents[2] / "yosai_intel_dashboard" / "src" / "services"
)
services_pkg = types.ModuleType("services")
services_pkg.__path__ = [str(services_root)]
safe_import("services", services_pkg)

upload_pkg = types.ModuleType("services.upload")
upload_pkg.__path__ = [str(services_root / "upload")]
safe_import("services.upload", upload_pkg)

protocols_mod = types.ModuleType("services.upload.protocols")
safe_import("services.upload.protocols", protocols_mod)

data_processing_pkg = types.ModuleType("services.data_processing")
data_processing_pkg.__path__ = [str(services_root / "data_processing")]
safe_import("services.data_processing", data_processing_pkg)

spec = importlib.util.spec_from_file_location(
    "services.data_processing.async_file_processor",
    services_root / "data_processing" / "async_file_processor.py",
)
async_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(async_mod)
AsyncFileProcessor = async_mod.AsyncFileProcessor


def test_process_file_failure_logs_and_cleans(monkeypatch, caplog):
    proc = AsyncFileProcessor()
    data_uri = "data:text/plain;base64," + base64.b64encode(b"foo").decode()
    original_unlink = os.unlink
    called = {}

    def fake_unlink(path):
        called["path"] = path
        original_unlink(path)

    monkeypatch.setattr(os, "unlink", fake_unlink)

    async def run():
        with caplog.at_level(logging.ERROR):
            with pytest.raises(FileProcessingError):
                await proc.process_file(data_uri, "bad.txt")

    asyncio.run(run())

    assert called
    record = next(r for r in caplog.records if r.levelname == "ERROR")
    assert "Processing failed" in record.message
    assert uuid.UUID(getattr(record, "correlation_id"))


def test_process_file_cancelled_logs_and_cleans(monkeypatch, caplog):
    proc = AsyncFileProcessor()

    async def slow_load_csv(*args, **kwargs):
        await asyncio.sleep(1)
        return pd.DataFrame()

    monkeypatch.setattr(proc, "load_csv", slow_load_csv)
    contents = "data:text/csv;base64," + base64.b64encode(b"a,b\n1,2").decode()
    original_unlink = os.unlink
    called = {}

    def fake_unlink(path):
        called["path"] = path
        original_unlink(path)

    monkeypatch.setattr(os, "unlink", fake_unlink)

    async def run():
        task = asyncio.create_task(proc.process_file(contents, "file.csv"))
        await asyncio.sleep(0.1)
        with caplog.at_level(logging.WARNING):
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(run())

    assert called
    record = next(r for r in caplog.records if r.levelname == "WARNING")
    assert "Processing cancelled" in record.message
    assert uuid.UUID(getattr(record, "correlation_id"))
