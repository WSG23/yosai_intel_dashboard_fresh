import base64
import importlib.util
import sys
import types
from pathlib import Path

import pytest
from tests.fixtures import MockCallbackManager, MockUploadDataStore

# Stubs to avoid heavy dependencies
sys.modules['yosai_intel_dashboard.src.infrastructure.callbacks.events'] = types.SimpleNamespace(CallbackEvent=object)
sys.modules['yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks'] = types.SimpleNamespace(TrulyUnifiedCallbacks=object)
sys.modules['yosai_intel_dashboard.src.core.unicode'] = types.SimpleNamespace(UnicodeProcessor=types.SimpleNamespace(sanitize_dataframe=lambda df: df))
sys.modules['yosai_intel_dashboard.src.infrastructure.config.dynamic_config'] = types.SimpleNamespace(dynamic_config=types.SimpleNamespace(security=types.SimpleNamespace(max_upload_mb=1)))
sys.modules['yosai_intel_dashboard.src.utils'] = types.ModuleType('yosai_intel_dashboard.src.utils')
san_stub = types.ModuleType('yosai_intel_dashboard.src.utils.sanitization')
san_stub.sanitize_text = lambda x: x
sys.modules['yosai_intel_dashboard.src.utils.sanitization'] = san_stub

afh = types.ModuleType('yosai_intel_dashboard.src.services.data_processing.file_handler')
class FileHandler:
    def validate_file(self, contents, filename):
        return types.SimpleNamespace(columns=[], memory_usage=lambda deep: [0])
afh.FileHandler = FileHandler
sys.modules['yosai_intel_dashboard.src.services.data_processing.file_handler'] = afh

astore = types.ModuleType('yosai_intel_dashboard.src.utils.upload_store')
astore.UploadedDataStore = MockUploadDataStore
sys.modules['yosai_intel_dashboard.src.utils.upload_store'] = astore

spec = importlib.util.spec_from_file_location('ufc', Path('yosai_intel_dashboard/src/services/unified_file_controller.py'))
ufc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ufc)


def test_disallowed_extension(tmp_path):
    manager = MockCallbackManager()
    store = MockUploadDataStore(storage_dir=tmp_path)
    csv_bytes = b"a,b\n1,2"
    b64 = base64.b64encode(csv_bytes).decode()
    content = f"data:text/csv;base64,{b64}"
    with pytest.raises(ValueError):
        ufc.process_file_upload(content, "bad.exe", callback_manager=manager, storage=store)
