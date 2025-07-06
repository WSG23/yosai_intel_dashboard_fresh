import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import importlib
import types
# Stub heavy dependencies so pages.file_upload can be imported without extras
stub_pandas = types.ModuleType('pandas')
stub_pandas.DataFrame = object
sys.modules['pandas'] = stub_pandas
sys.modules['yaml'] = types.ModuleType('yaml')
sys.modules['analytics.controllers'] = types.ModuleType('analytics.controllers')
sys.modules['analytics.controllers'].UnifiedAnalyticsController = object
sys.modules['core.dash_profile'] = types.ModuleType('core.dash_profile')
sys.modules['core.dash_profile'].profile_callback = lambda *a, **kw: (lambda f: f)
sys.modules['core.callback_registry'] = types.ModuleType('core.callback_registry')
sys.modules['core.callback_registry'].debounce = lambda *a, **kw: (lambda f: f)
cfg_mod = types.ModuleType('config.config')
class _Cfg: max_display_rows = 100
cfg_mod.get_analytics_config = lambda: _Cfg()
sys.modules['config.config'] = cfg_mod
dyn_mod = types.ModuleType('config.dynamic_config')
class _Dyn:
    def get_max_upload_size_bytes(self):
        return 1024
dyn_mod.dynamic_config = _Dyn()
sys.modules['config.dynamic_config'] = dyn_mod
sys.modules['services.device_learning_service'] = types.ModuleType('services.device_learning_service')
sys.modules['services.device_learning_service'].get_device_learning_service = lambda: None
uds_mod = types.ModuleType('utils.upload_store')
uds_mod.uploaded_data_store = object()
sys.modules['utils.upload_store'] = uds_mod
uds = types.ModuleType('services.upload_data_service')
uds.get_uploaded_data = lambda: {}
uds.get_uploaded_filenames = lambda: []
uds.clear_uploaded_data = lambda: None
uds.get_file_info = lambda: {}
sys.modules['services.upload_data_service'] = uds
col_mod = types.ModuleType('components.column_verification')
sys.modules["services.analytics_service"] = types.ModuleType("services.analytics_service")
sys.modules["services.analytics_service"].MAX_DISPLAY_ROWS = 10
sys.modules["services.analytics_service"].UploadAnalyticsProcessor = object
sys.modules["services.analytics"] = types.ModuleType("services.analytics")
sys.modules["services.analytics.upload_analytics"] = types.ModuleType("services.analytics.upload_analytics")

col_mod.save_verified_mappings = lambda *a, **k: None
sys.modules['components.column_verification'] = col_mod
upload_mod = types.ModuleType('services.upload')
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
upload_mod.get_trigger_id = lambda: 'trig'
validators_mod = types.ModuleType("services.upload.validators")
validators_mod.ClientSideValidator = lambda *a, **k: None
sys.modules["services.upload.validators"] = validators_mod
upload_mod.save_ai_training_data = lambda *a, **k: None
sys.modules['services.upload'] = upload_mod
comp_mod = types.ModuleType('components.upload')
comp_mod.ClientSideValidator = lambda *a, **k: None
sys.modules['components.upload'] = comp_mod
task_mod = types.ModuleType('services.task_queue')
async def _create_task(coro):
    if hasattr(coro, 'close'):
        coro.close()
    return 'tid'
task_mod.create_task = _create_task
task_mod.get_status = lambda tid: {'progress': 0}
task_mod.clear_task = lambda tid: None
sys.modules['services.task_queue'] = task_mod
sys.modules['pages.graphs'] = types.ModuleType('pages.graphs')
sys.modules['pages.graphs'].GRAPH_FIGURES = {}
sys.modules['pages.deep_analytics'] = types.ModuleType('pages.deep_analytics')
sys.modules['pages.export'] = types.ModuleType('pages.export')
sys.modules['pages.settings'] = types.ModuleType('pages.settings')

# Now import the module under test
pu = importlib.import_module('pages.file_upload')


def test_layout_reexport():
    layout_mod = importlib.import_module('pages.file_upload.layout')
    assert pu.layout is layout_mod.layout


def test_callbacks_reexport():
    cb_mod = importlib.import_module('pages.file_upload.callbacks')
    assert pu.Callbacks is cb_mod.Callbacks
    assert pu.register_upload_callbacks is cb_mod.register_upload_callbacks


def test_callbacks_methods():
    cb_mod = importlib.import_module('pages.file_upload.callbacks')
    assert hasattr(cb_mod.Callbacks, 'schedule_upload_task')
