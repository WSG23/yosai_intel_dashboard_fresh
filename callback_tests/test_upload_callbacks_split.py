import importlib
import sys
import types
from dash import no_update
from upload_core import UploadCore

sys.modules["pages.graphs"] = types.ModuleType("pages.graphs")
sys.modules["pages.graphs"].GRAPH_FIGURES = {}

file_upload = importlib.import_module("pages.file_upload")
Callbacks = UploadCore


def test_schedule_upload_task_none():
    cb = Callbacks()
    assert cb.schedule_upload_task(None, None) == ""


def test_schedule_upload_task(monkeypatch):
    cb = Callbacks()
    recorded = {}

    def fake_create_task(coro):
        recorded['called'] = isinstance(coro, types.CoroutineType)
        return "tid42"

    monkeypatch.setattr("pages.file_upload.create_task", fake_create_task)
    tid = cb.schedule_upload_task("content", "f.csv")
    assert tid == "tid42"
    assert recorded['called']


def test_reset_upload_progress_disabled():
    cb = Callbacks()
    assert cb.reset_upload_progress(None) == (0, "0%", True)


def test_reset_upload_progress_enabled():
    cb = Callbacks()
    assert cb.reset_upload_progress("data") == (0, "0%", False)


def test_update_progress_bar(monkeypatch):
    cb = Callbacks()
    monkeypatch.setattr("pages.file_upload.get_status", lambda tid: {"progress": 55})
    assert cb.update_progress_bar(1, "tid") == (55, "55%")


def test_finalize_upload_results_not_done(monkeypatch):
    cb = Callbacks()
    monkeypatch.setattr("pages.file_upload.get_status", lambda tid: {"progress": 5})
    assert cb.finalize_upload_results(1, "tid") == (no_update,) * 8


def test_finalize_upload_results_done(monkeypatch):
    cb = Callbacks()
    result = (1, 2, 3, 4, 5, 6, 7)
    monkeypatch.setattr("pages.file_upload.get_status", lambda tid: {"done": True, "result": result})
    called = {}
    monkeypatch.setattr("pages.file_upload.clear_task", lambda tid: called.setdefault('tid', tid))
    out = cb.finalize_upload_results(1, "tid")
    assert out == (*result, True)
    assert called['tid'] == "tid"
