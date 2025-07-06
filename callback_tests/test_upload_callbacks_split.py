import importlib
import sys
import types
from dash import no_update

stub_pandas = types.ModuleType("pandas")
stub_pandas.DataFrame = object
sys.modules["pandas"] = stub_pandas
sys.modules["yaml"] = types.ModuleType("yaml")
sys.modules["analytics.controllers"] = types.ModuleType("analytics.controllers")
sys.modules["analytics.controllers"].UnifiedAnalyticsController = object
sys.modules["core.dash_profile"] = types.ModuleType("core.dash_profile")
sys.modules["core.dash_profile"].profile_callback = lambda *a, **kw: (lambda f: f)
sys.modules["core.callback_registry"] = types.ModuleType("core.callback_registry")
sys.modules["core.callback_registry"].debounce = lambda *a, **kw: (lambda f: f)
cfg_mod = types.ModuleType("config.config")
class _Cfg: max_display_rows = 100
cfg_mod.get_analytics_config = lambda: _Cfg()
sys.modules["config.config"] = cfg_mod
dyn_mod = types.ModuleType("config.dynamic_config")
class _Dyn:
    def get_max_upload_size_bytes(self):
        return 1024
dyn_mod.dynamic_config = _Dyn()
sys.modules["config.dynamic_config"] = dyn_mod
sys.modules["services.device_learning_service"] = types.ModuleType("services.device_learning_service")
sys.modules["services.device_learning_service"].get_device_learning_service = lambda: None
uds_mod = types.ModuleType("utils.upload_store")
uds_mod.uploaded_data_store = object()
sys.modules["utils.upload_store"] = uds_mod
uds = types.ModuleType("services.upload_data_service")
uds.get_uploaded_data = lambda: {}
uds.get_uploaded_filenames = lambda: []
uds.clear_uploaded_data = lambda: None
uds.get_file_info = lambda: {}
sys.modules["services.upload_data_service"] = uds
col_mod = types.ModuleType("components.column_verification")
col_mod.save_verified_mappings = lambda *a, **k: None
sys.modules["components.column_verification"] = col_mod
upload_mod = types.ModuleType("services.upload")
class _Proc:
    async_processor = None
    def __init__(self, store):
        pass
    async def process_files(self, *a, **k):
        return ([], [], {}, [], {}, None, None)
class _AI:
    pass
class _Modal:
    pass
upload_mod.UploadProcessingService = _Proc
upload_mod.AISuggestionService = _AI
upload_mod.ModalService = _Modal
upload_mod.get_trigger_id = lambda: "trig"
upload_mod.save_ai_training_data = lambda *a, **k: None
sys.modules["services.upload"] = upload_mod
comp_mod = types.ModuleType("components.upload")
comp_mod.ClientSideValidator = lambda *a, **k: None
sys.modules["components.upload"] = comp_mod
task_mod = types.ModuleType("services.task_queue")
def _create_task(coro):
    if hasattr(coro, "close"):
        coro.close()
    return "tid"
task_mod.create_task = _create_task
task_mod.get_status = lambda tid: {"progress": 0}
task_mod.clear_task = lambda tid: None
sys.modules["services.task_queue"] = task_mod
sys.modules["pages.graphs"] = types.ModuleType("pages.graphs")
sys.modules["pages.graphs"].GRAPH_FIGURES = {}
sys.modules["pages.deep_analytics"] = types.ModuleType("pages.deep_analytics")
sys.modules["pages.export"] = types.ModuleType("pages.export")
sys.modules["pages.settings"] = types.ModuleType("pages.settings")

file_upload = importlib.import_module("pages.file_upload")
Callbacks = file_upload.Callbacks


def test_schedule_upload_task_none():
    cb = Callbacks()
    assert cb.schedule_upload_task(None, None) == ""


def test_schedule_upload_task(monkeypatch):
    cb = Callbacks()
    recorded = {}

    def fake_create_task(coro):
        recorded['called'] = isinstance(coro, types.CoroutineType)
        if hasattr(coro, "close"):
            coro.close()
        return "tid42"

    monkeypatch.setattr("pages.file_upload.create_task", fake_create_task)
    tid = cb.schedule_upload_task("content", "f.csv")
    assert tid == "tid42"
    assert recorded['called']


def test_schedule_upload_task_returns_non_empty(monkeypatch):
    cb = Callbacks()
    def fake_create_task(coro):
        if hasattr(coro, "close"):
            coro.close()
        return "tid99"

    monkeypatch.setattr("pages.file_upload.create_task", fake_create_task)
    tid = cb.schedule_upload_task("data", "name.csv")
    assert isinstance(tid, str) and tid


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
