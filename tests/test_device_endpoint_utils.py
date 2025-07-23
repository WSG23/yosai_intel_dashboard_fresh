import sys
import types
import pandas as pd

# Provide lightweight stubs required for importing device_endpoint
core_container_stub = types.ModuleType("core.container")
core_container_stub.container = types.SimpleNamespace(
    has=lambda name: True,
    get=lambda name: None,
)
service_reg_stub = types.ModuleType("config.service_registration")
service_reg_stub.register_upload_services = lambda c: None
sys.modules.setdefault("core.container", core_container_stub)
sys.modules.setdefault("config.service_registration", service_reg_stub)

# Allow importing submodules from the real "services" package
services_mod = sys.modules.setdefault("services", types.ModuleType("services"))
services_mod.__path__ = [str((__file__)).rsplit("/tests/", 1)[0] + "/services"]

from device_endpoint import (
    load_stored_data,
    determine_device_column,
    build_device_mappings,
)

class DummyUploadService:
    def __init__(self, df_map):
        self.store = types.SimpleNamespace(get_all_data=lambda: df_map)
    def auto_apply_learned_mappings(self, df, filename):
        return False

class DummyDeviceService:
    def __init__(self, user_map=None):
        self.user_map = user_map or {}
    def get_user_device_mappings(self, filename):
        return self.user_map


def test_load_stored_data_found():
    df = pd.DataFrame({"a": [1]})
    svc = DummyUploadService({"file.csv": df})
    out = load_stored_data("file.csv", svc)
    assert out is df


def test_load_stored_data_missing():
    svc = DummyUploadService({})
    out = load_stored_data("missing.csv", svc)
    assert out is None


def test_determine_device_column():
    df = pd.DataFrame({"host": ["a"], "val": [1]})
    col = determine_device_column({"host": "device"}, df)
    assert col == "host"


def test_determine_device_column_none():
    df = pd.DataFrame({"host": ["a"]})
    col = determine_device_column({"other": "device"}, df)
    assert col is None


def test_build_device_mappings_user():
    df = pd.DataFrame({})
    dsvc = DummyDeviceService({"dev": {"device_type": "door"}})
    usvc = DummyUploadService({})
    mapping = build_device_mappings("f.csv", df, dsvc, usvc)
    assert mapping["dev"]["device_type"] == "door"
    assert mapping["dev"]["source"] == "user_confirmed"


def test_build_device_mappings_ai(monkeypatch):
    df = pd.DataFrame({})
    dsvc = DummyDeviceService()
    ai_map = {"dev": {"device_type": "door", "confidence": 0.7}}
    from services.ai_mapping_store import ai_mapping_store
    monkeypatch.setattr(ai_mapping_store, "clear", lambda: None)
    monkeypatch.setattr(ai_mapping_store, "all", lambda: ai_map)
    usvc = DummyUploadService({})
    monkeypatch.setattr(usvc, "auto_apply_learned_mappings", lambda df, fn: False)
    sdm_stub = types.ModuleType("components.simple_device_mapping")
    sdm_stub.generate_ai_device_defaults = lambda df, profile="auto": None
    components_pkg = types.ModuleType("components")
    components_pkg.simple_device_mapping = sdm_stub
    sys.modules["components"] = components_pkg
    sys.modules["components.simple_device_mapping"] = sdm_stub
    mapping = build_device_mappings("f.csv", df, dsvc, usvc)
    assert mapping["dev"]["source"] == "ai_suggested"
