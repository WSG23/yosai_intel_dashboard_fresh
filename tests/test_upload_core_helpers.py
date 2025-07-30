import types
import base64
import pandas as pd
from dash import no_update

from services.upload.upload_core_helpers import (
    process_uploaded_files_helper,
    finalize_upload_results_helper,
    save_confirmed_device_mappings_helper,
)


class DummyProcessing:
    def __init__(self):
        self.calls = []

    async def process_files(self, contents, filenames):
        self.calls.append((contents, filenames))
        return ([], [], {filenames[0]: {"rows": len(contents)}}, [], {}, no_update, no_update)

    def build_failure_alert(self, msg):
        return {"alert": msg}


class DummyValidator:
    def validate_file_upload(self, _c):
        return types.SimpleNamespace(valid=True, message="")


class DummyChunked:
    def __init__(self):
        self.progress = {}

    def start_file(self, name):
        self.progress[name] = 0

    def finish_file(self, name):
        self.progress[name] = 100

    def get_progress(self, name):
        return self.progress.get(name, 0)


class DummyQueue:
    def __init__(self):
        self.files = []

    def add_file(self, name):
        self.files.append(name)

    def mark_complete(self, name):
        pass


class DummyTaskQueue:
    def __init__(self, status):
        self.status = status
        self.cleared = False

    def get_status(self, _tid):
        return self.status

    def clear_task(self, _tid):
        self.cleared = True


class DummyStore(FakeUploadStore):
    pass


class DummyCore:
    def __init__(self, status=None):
        self.validator = DummyValidator()
        self.processing = DummyProcessing()
        self.chunked = DummyChunked()
        self.queue = DummyQueue()
        self.task_queue = DummyTaskQueue(status or {})
        self.store = DummyStore()
        self.learning_service = FakeDeviceLearningService()
        self.rabbitmq = None


def test_process_uploaded_files_helper(async_runner):
    df = pd.DataFrame({"A": [1, 2]})
    csv = df.to_csv(index=False).encode()
    content = "data:text/csv;base64," + base64.b64encode(csv).decode()
    core = DummyCore()
    out = async_runner(process_uploaded_files_helper(core, [content], ["sample.csv"]))
    info = out[2]
    assert info["sample.csv"]["rows"] == 1


def test_finalize_upload_results_helper_done(monkeypatch):
    core = DummyCore(status={"done": True, "result": (1, 2, 3, 4, 5, 6, 7)})
    called = {}
    monkeypatch.setattr(
        "components.simple_device_mapping.generate_ai_device_defaults",
        lambda df, profile="auto": called.setdefault("gen", True),
    )
    out = finalize_upload_results_helper(core, 1, "tid")
    assert out[-1] is True
    assert core.task_queue.cleared
    assert called.get("gen") is True


def test_save_confirmed_device_mappings_helper(monkeypatch):
    core = DummyCore()
    df = pd.DataFrame({"A": [1]})
    core.store.add_file("f.csv", df)
    monkeypatch.setattr("services.ai_mapping_store.ai_mapping_store.update", lambda m: None)
    file_info = {"devices": ["d1"], "filename": "f.csv"}
    res = save_confirmed_device_mappings_helper(core, True, [1], [5], [[]], [[]], file_info)
    assert res[1] is False
