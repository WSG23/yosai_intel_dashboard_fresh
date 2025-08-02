import base64
import importlib.util
import sys
import types
from pathlib import Path

import pandas as pd
import asyncio
import tempfile
import os
from tests.import_helpers import safe_import, import_optional

# Set up minimal stub modules for dependencies
config_mod = types.SimpleNamespace()
config_mod.dynamic_config = types.SimpleNamespace(
    analytics=types.SimpleNamespace(chunk_size=2, max_memory_mb=1024)
)
safe_import('config.dynamic_config', config_mod)
sys.modules.setdefault(
    "core.protocols",
    types.SimpleNamespace(FileProcessorProtocol=object),
)
sys.modules.setdefault(
    "services.rabbitmq_client",
    types.SimpleNamespace(RabbitMQClient=lambda *a, **k: None),
)
sys.modules.setdefault(
    "services.task_queue",
    types.SimpleNamespace(
        create_task=lambda *a, **k: "id",
        get_status=lambda *a, **k: {"progress": 0},
    ),
)
sys.modules.setdefault(
    "utils.memory_utils",
    types.SimpleNamespace(check_memory_limit=lambda *a, **k: None),
)
sys.modules.setdefault(
    "services.data_processing.file_processor",
    types.SimpleNamespace(
        UnicodeFileProcessor=types.SimpleNamespace(
            sanitize_dataframe_unicode=lambda df: df
        )
    ),
)

services_root = Path(__file__).resolve().parents[2] / "services"
spec = importlib.util.spec_from_file_location(
    "services.data_processing.async_file_processor",
    services_root / "data_processing" / "async_file_processor.py",
)
async_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(async_mod)
AsyncFileProcessor = async_mod.AsyncFileProcessor
cfg = config_mod.dynamic_config


def _setup_temp_patches(monkeypatch, stored_data):
    def fake_mkstemp(suffix=""):
        return (99, f"/virtual/tmp{suffix}")

    monkeypatch.setattr(tempfile, "mkstemp", fake_mkstemp)
    monkeypatch.setattr(os, "close", lambda fd: None)
    monkeypatch.setattr(
        os,
        "unlink",
        lambda path: stored_data.pop(str(path), None),
    )

    def fake_write_bytes(self, data):
        stored_data[str(self)] = data
        return len(data)

    monkeypatch.setattr(Path, "write_bytes", fake_write_bytes)
    monkeypatch.setattr(
        async_mod.AsyncFileProcessor,
        "_count_lines",
        lambda self, path: 2,
    )


def test_process_file_csv_no_disk(monkeypatch):
    raw = b"a,b\n1,x\n2,y\n"
    data_uri = "data:text/csv;base64," + base64.b64encode(raw).decode()

    stored = {}
    _setup_temp_patches(monkeypatch, stored)

    expected = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})

    def fake_read_csv(path, chunksize=None, encoding="utf-8"):
        assert stored[str(path)] == raw
        if chunksize:
            # emulate chunked reading
            return iter([expected.iloc[:1], expected.iloc[1:]])
        return expected

    monkeypatch.setattr(pd, "read_csv", fake_read_csv)

    proc = AsyncFileProcessor(config=cfg)
    progress = []
    result = asyncio.run(
        proc.process_file(
            data_uri, "test.csv", progress_callback=lambda _f, p: progress.append(p)
        )
    )

    assert result.equals(expected)
    assert progress and progress[-1] == 100
    assert stored == {}


def test_process_file_excel_no_disk(monkeypatch):
    raw = b"FAKEEXCELDATA"
    data_uri = (
        "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,"
        + base64.b64encode(raw).decode()
    )

    stored = {}
    _setup_temp_patches(monkeypatch, stored)

    expected = pd.DataFrame({"c": [5, 6]})

    def fake_read_excel(path):
        assert stored[str(path)] == raw
        return expected

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)

    proc = AsyncFileProcessor(config=cfg)
    progress = []
    result = asyncio.run(
        proc.process_file(
            data_uri, "file.xlsx", progress_callback=lambda _f, p: progress.append(p)
        )
    )

    assert result.equals(expected)
    assert progress and progress[-1] == 100
    assert stored == {}


def test_process_file_json_no_disk(monkeypatch):
    raw = b"[{\"x\": 1}, {\"x\": 2}]"
    data_uri = "data:application/json;base64," + base64.b64encode(raw).decode()

    stored = {}
    _setup_temp_patches(monkeypatch, stored)

    expected = pd.DataFrame({"x": [1, 2]})

    def fake_read_json(path):
        assert stored[str(path)] == raw
        return expected

    monkeypatch.setattr(pd, "read_json", fake_read_json)

    proc = AsyncFileProcessor(config=cfg)
    progress = []
    result = asyncio.run(
        proc.process_file(
            data_uri, "file.json", progress_callback=lambda _f, p: progress.append(p)
        )
    )

    assert result.equals(expected)
    assert progress and progress[-1] == 100
    assert stored == {}
