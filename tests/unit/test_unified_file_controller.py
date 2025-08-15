from __future__ import annotations

import os
import asyncio
import inspect
import sys
import types
from enum import Enum, auto
from pathlib import Path
import base64
import io

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "pass")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("ANALYTICS_API_KEY", "dummy")

from yosai_intel_dashboard.src.core.imports.resolver import safe_import  # noqa: E402
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder  # noqa: E402
from tests.fixtures import MockUploadDataStore  # noqa: E402

callback_events_stub = types.ModuleType("core.callback_events")


class CallbackEvent(Enum):
    FILE_UPLOAD_COMPLETE = auto()
    DATA_PROCESSED = auto()


callback_events_stub.CallbackEvent = CallbackEvent
safe_import("core.callback_events", callback_events_stub)

# Stub heavy dependencies used during module import
sys.modules[
    "yosai_intel_dashboard.src.core.unicode"
] = types.SimpleNamespace(UnicodeProcessor=types.SimpleNamespace(sanitize_dataframe=lambda df: df))
sys.modules[
    "yosai_intel_dashboard.src.infrastructure.config.dynamic_config"
] = types.SimpleNamespace(dynamic_config=types.SimpleNamespace(security=types.SimpleNamespace(max_upload_mb=10)))
sys.modules[
    "yosai_intel_dashboard.src.utils.sanitization"
] = types.SimpleNamespace(sanitize_text=lambda x: x)

afh = types.ModuleType("yosai_intel_dashboard.src.services.data_processing.file_handler")

class FileHandler:
    def validate_file(self, contents, filename):
        import pandas as pd
        csv_bytes = base64.b64decode(contents.split(",", 1)[1])
        return pd.read_csv(io.BytesIO(csv_bytes))

afh.FileHandler = FileHandler
sys.modules[
    "yosai_intel_dashboard.src.services.data_processing.file_handler"
] = afh

upload_stub = types.ModuleType("yosai_intel_dashboard.src.utils.upload_store")
upload_stub.UploadedDataStore = MockUploadDataStore
sys.modules[
    "yosai_intel_dashboard.src.utils.upload_store"
] = upload_stub


class DummyManager:
    def __init__(self) -> None:
        self.events = {}

    def register_event(self, event, func, **_):
        self.events.setdefault(event, []).append(func)

    def trigger(self, event, *args, **kwargs):
        results = []
        for cb in self.events.get(event, []):
            if inspect.iscoroutinefunction(cb):
                results.append(asyncio.run(cb(*args, **kwargs)))
            else:
                results.append(cb(*args, **kwargs))
        return results

    async def trigger_async(self, event, *args, **kwargs):
        tasks = []
        for cb in self.events.get(event, []):
            if inspect.iscoroutinefunction(cb):
                tasks.append(asyncio.create_task(cb(*args, **kwargs)))
            else:
                tasks.append(asyncio.to_thread(cb, *args, **kwargs))
        return await asyncio.gather(*tasks)


tuc_stub = types.ModuleType(
    "yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks"
)
tuc_stub.TrulyUnifiedCallbacks = DummyManager
sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks",
    tuc_stub,
)

from yosai_intel_dashboard.src.services.unified_file_controller import (  # noqa: E402
    register_callbacks,
)


def test_register_callbacks_processes_upload(tmp_path):
    manager = DummyManager()
    store = MockUploadDataStore(storage_dir=tmp_path)
    df = DataFrameBuilder().add_column("a", [1, 2]).build()
    content = UploadFileBuilder().with_dataframe(df).as_base64()

    events = []
    manager.register_event(
        CallbackEvent.DATA_PROCESSED,
        lambda source, data: events.append((source, data)),
    )

    register_callbacks(manager)

    manager.trigger(
        CallbackEvent.FILE_UPLOAD_COMPLETE, content, "sample.csv", storage=store
    )

    saved = store.load_dataframe("sample.csv")
    assert saved.equals(df)
    assert events and events[0][1]["rows"] == 2
