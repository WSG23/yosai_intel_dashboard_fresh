import sys
import types
from pathlib import Path
from tests.import_helpers import safe_import, import_optional

safe_import('yosai_intel_dashboard', types.ModuleType("yosai_intel_dashboard"))
sys.modules["yosai_intel_dashboard"].__path__ = [str(Path(__file__).resolve().parents[1] / "yosai_intel_dashboard")]

import pandas as pd

# Provide lightweight stubs required for importing device_endpoint
core_container_stub = types.ModuleType("core.container")
core_container_stub.container = types.SimpleNamespace(
    has=lambda name: True,
    get=lambda name: None,
    register_singleton=lambda *args, **kwargs: None,
)
service_reg_stub = types.ModuleType("services.upload.service_registration")
service_reg_stub.register_upload_services = lambda c: c.register_singleton(
    "uploader", object()
)
safe_import('core.container', core_container_stub)
safe_import('services.upload.service_registration', service_reg_stub)

# Allow importing submodules from the real "services" package
services_mod = sys.modules.setdefault("services", types.ModuleType("services"))
services_mod.__path__ = [str((__file__)).rsplit("/tests/", 1)[0] + "/services"]

from yosai_intel_dashboard.src.services.device_endpoint import (
    build_ai_device_mappings,
    build_device_mappings,
    build_user_device_mappings,
    determine_device_column,
    load_stored_data,
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
    sdm_stub = types.ModuleType(
        "yosai_intel_dashboard.src.components.simple_device_mapping"
    )
    sdm_stub.generate_ai_device_defaults = lambda df, profile="auto": None
    components_pkg = types.ModuleType("yosai_intel_dashboard.src.components")
    components_pkg.simple_device_mapping = sdm_stub
    safe_import('yosai_intel_dashboard.src.components', components_pkg)
    sys.modules[
        "yosai_intel_dashboard.src.components.simple_device_mapping"
    ] = sdm_stub
    mapping = build_device_mappings("f.csv", df, dsvc, usvc)
    assert mapping["dev"]["source"] == "ai_suggested"


def test_build_user_device_mappings_helper():
    user_map = {"dev": {"device_type": "door", "properties": {"a": 1}}}
    result = build_user_device_mappings(user_map)
    assert result["dev"]["device_type"] == "door"
    assert result["dev"]["confidence"] == 1.0
    assert result["dev"]["source"] == "user_confirmed"


def test_build_ai_device_mappings_helper(monkeypatch):
    df = pd.DataFrame({})
    ai_map = {"dev": {"device_type": "door", "confidence": 0.7}}
    from services.ai_mapping_store import ai_mapping_store

    monkeypatch.setattr(ai_mapping_store, "clear", lambda: None)
    monkeypatch.setattr(ai_mapping_store, "all", lambda: ai_map)
    usvc = DummyUploadService({})
    monkeypatch.setattr(usvc, "auto_apply_learned_mappings", lambda df, fn: False)
    sdm_stub = types.ModuleType(
        "yosai_intel_dashboard.src.components.simple_device_mapping"
    )
    sdm_stub.generate_ai_device_defaults = lambda df, profile="auto": None
    components_pkg = types.ModuleType("yosai_intel_dashboard.src.components")
    components_pkg.simple_device_mapping = sdm_stub
    safe_import('yosai_intel_dashboard.src.components', components_pkg)
    sys.modules[
        "yosai_intel_dashboard.src.components.simple_device_mapping"
    ] = sdm_stub
    mapping = build_ai_device_mappings(df, "f.csv", usvc)
    assert mapping["dev"]["source"] == "ai_suggested"
