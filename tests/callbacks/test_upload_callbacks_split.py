import types

import pytest
from dash import no_update

from services.upload.processor import UploadProcessingService
from services.upload.upload_core import UploadCore
from tests.fakes import (
    FakeDeviceLearningService,
    FakeUploadDataService,
    FakeUploadStore,
)


def _create_core(monkeypatch=None):
    store = FakeUploadStore()
    learning = FakeDeviceLearningService()
    data_svc = FakeUploadDataService(store)
    processing = UploadProcessingService(store, learning, data_svc)
    core = UploadCore(processing, learning, store)
    if monkeypatch is not None:
        monkeypatch.setattr(
            "services.device_learning_service.get_device_learning_service",
            lambda: FakeDeviceLearningService(),
        )
    return core


def test_schedule_upload_task_none(monkeypatch):
    cb = _create_core(monkeypatch)
    assert cb.schedule_upload_task(None, None) == ""


def test_schedule_upload_task(monkeypatch):
    cb = _create_core(monkeypatch)

    recorded = {}

    def fake_create_task(coro):
        recorded["called"] = isinstance(coro, types.CoroutineType)
        if hasattr(coro, "close"):
            coro.close()
        return "tid42"

    monkeypatch.setattr("services.upload.upload_core.create_task", fake_create_task)
    tid = cb.schedule_upload_task("content", "f.csv")
    assert tid == "tid42"
    assert recorded["called"]


def test_schedule_upload_task_returns_non_empty(monkeypatch):
    cb = _create_core(monkeypatch)

    def fake_create_task(coro):
        if hasattr(coro, "close"):
            coro.close()
        return "tid99"

    monkeypatch.setattr("services.upload.upload_core.create_task", fake_create_task)
    tid = cb.schedule_upload_task("data", "name.csv")
    assert isinstance(tid, str) and tid


def test_schedule_upload_task_triggers_event(monkeypatch):
    cb = _create_core(monkeypatch)

    def fake_create(coro):
        if hasattr(coro, "close"):
            coro.close()
        return "tid77"

    monkeypatch.setattr("services.upload.upload_core.create_task", fake_create)
    tid = cb.schedule_upload_task("data", "name.csv")
    assert tid == "tid77"
    assert isinstance(tid, str)


def test_schedule_upload_task_error(monkeypatch):
    cb = _create_core(monkeypatch)

    def boom(coro):
        if hasattr(coro, "close"):
            coro.close()
        raise RuntimeError("fail")

    monkeypatch.setattr("services.upload.upload_core.create_task", boom)
    with pytest.raises(RuntimeError):
        cb.schedule_upload_task("data", "name.csv")


def test_reset_upload_progress_disabled(monkeypatch):
    cb = _create_core(monkeypatch)
    assert cb.reset_upload_progress(None) == (0, "0%", True)


def test_reset_upload_progress_enabled(monkeypatch):
    cb = _create_core(monkeypatch)
    assert cb.reset_upload_progress("data") == (0, "0%", False)


def test_update_progress_bar(monkeypatch):
    cb = _create_core(monkeypatch)

    cb.queue = types.SimpleNamespace(files=[])
    cb.chunked = types.SimpleNamespace(get_progress=lambda _n: 0)
    monkeypatch.setattr(cb.task_queue, "get_status", lambda tid: {"progress": 55})
    assert cb.update_progress_bar(1, "tid") == (55, "55%", [])


def test_finalize_upload_results_not_done(monkeypatch):
    cb = _create_core(monkeypatch)
    monkeypatch.setattr(cb.task_queue, "get_status", lambda tid: {"progress": 5})
    assert cb.finalize_upload_results(1, "tid") == (no_update,) * 8


def test_finalize_upload_results_done(monkeypatch):
    cb = _create_core(monkeypatch)

    result = (1, 2, 3, 4, 5, 6, 7)
    monkeypatch.setattr(
        cb.task_queue, "get_status", lambda tid: {"done": True, "result": result}
    )
    called = {}
    monkeypatch.setattr(
        cb.task_queue, "clear_task", lambda tid: called.setdefault("tid", tid)
    )
    monkeypatch.setattr(
        "components.simple_device_mapping.generate_ai_device_defaults",
        lambda df, profile="auto": called.setdefault("gen", True),
    )
    out = cb.finalize_upload_results(1, "tid")
    assert out == (*result, True)
    assert called["tid"] == "tid"
    assert called.get("gen") is True
