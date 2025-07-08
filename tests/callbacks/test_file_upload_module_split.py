import importlib
import sys
import types
from pathlib import Path

# Ensure repository root is on the module search path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Stub dash modules so tests run without Dash installed
sys.modules['dash'] = types.ModuleType('dash')
sys.modules['dash.dcc'] = types.ModuleType('dash.dcc')
sys.modules['dash.html'] = types.ModuleType('dash.html')
sys.modules['dash.dash'] = types.ModuleType('dash.dash')
sys.modules['dash.dependencies'] = types.ModuleType('dash.dependencies')
sys.modules['dash_bootstrap_components'] = types.ModuleType('dash_bootstrap_components')

# Other dependencies required by pages.file_upload
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
class _Cfg:
    max_display_rows = 100
cfg_mod.get_analytics_config = lambda: _Cfg()
sys.modules['config.config'] = cfg_mod

dyn_mod = types.ModuleType('config.dynamic_config')
class _Dyn:
    def get_max_upload_size_bytes(self):
        return 1024
    security = types.SimpleNamespace(
        max_upload_mb=10,
        rate_limit_requests=100,
        rate_limit_window_minutes=1,
        time_window=60,
    )

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
col_mod.save_verified_mappings = lambda *a, **k: None
sys.modules['components.column_verification'] = col_mod

svc_analytics_service = types.ModuleType('services.analytics_service')
svc_analytics_service.MAX_DISPLAY_ROWS = 100
sys.modules['services.analytics_service'] = svc_analytics_service

core_unicode = types.ModuleType('core.unicode')
core_unicode.safe_unicode_decode = lambda x, **_: x
core_unicode.safe_unicode_encode = lambda x, **_: x
core_unicode.ChunkedUnicodeProcessor = type(
    'ChunkedUnicodeProcessor',
    (),
    {'process_large_content': staticmethod(lambda c, chunk_size=100: c)},
)
sys.modules['core.unicode'] = core_unicode

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
upload_mod.save_ai_training_data = lambda *a, **k: None
sys.modules['services.upload'] = upload_mod

validators_mod = types.ModuleType('services.upload.validators')
validators_mod.ClientSideValidator = lambda *a, **k: None
sys.modules['services.upload.validators'] = validators_mod

comp_mod = types.ModuleType('components.upload')
comp_mod.ClientSideValidator = lambda *a, **k: None
sys.modules['components.upload'] = comp_mod

task_mod = types.ModuleType('services.task_queue')

def _create_task(coro):
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

# Finally import the module under test
file_upload = importlib.import_module('pages.file_upload')


def test_module_imports():
    assert hasattr(file_upload, 'layout')
