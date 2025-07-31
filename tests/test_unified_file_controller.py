import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")
import pandas as pd
import types
from enum import Enum, auto
from utils.upload_store import UploadedDataStore
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder

callback_events_stub = types.ModuleType("core.callback_events")

class CallbackEvent(Enum):
    FILE_UPLOAD_COMPLETE = auto()
    DATA_PROCESSED = auto()

callback_events_stub.CallbackEvent = CallbackEvent
sys.modules.setdefault("core.callback_events", callback_events_stub)

tuc_stub = types.ModuleType("core.truly_unified_callbacks")
tuc_stub.TrulyUnifiedCallbacks = DummyManager
sys.modules.setdefault("core.truly_unified_callbacks", tuc_stub)

from yosai_intel_dashboard.src.services.unified_file_controller import register_callbacks


class DummyManager:
    def __init__(self) -> None:
        self.events = {}

    def register_event(self, event, func, **_):
        self.events.setdefault(event, []).append(func)

    def trigger(self, event, *args, **kwargs):
        return [cb(*args, **kwargs) for cb in self.events.get(event, [])]


def test_register_callbacks_processes_upload(tmp_path):
    manager = DummyManager()
    store = UploadedDataStore(storage_dir=tmp_path)
    df = DataFrameBuilder().add_column("a", [1, 2]).build()
    content = UploadFileBuilder().with_dataframe(df).as_base64()

    events = []
    manager.register_event(
        CallbackEvent.DATA_PROCESSED,
        lambda source, data: events.append((source, data)),
    )

    register_callbacks(manager)

    manager.trigger(CallbackEvent.FILE_UPLOAD_COMPLETE, content, "sample.csv", storage=store)

    saved = store.load_dataframe("sample.csv")
    assert saved.equals(df)
    assert events and events[0][1]["rows"] == 2
