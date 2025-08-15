import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")


class _DummyAIGen:
    def __init__(self, *a, **k):
        pass


class _DummyAttrs:
    pass


sys.modules.setdefault(
    "services.ai_device_generator", type(sys)("services.ai_device_generator")
)
sys.modules["services.ai_device_generator"].AIDeviceGenerator = _DummyAIGen
sys.modules["services.ai_device_generator"].DeviceAttributes = _DummyAttrs

from yosai_intel_dashboard.src.services.ai_device_generator import AIDeviceGenerator, DeviceAttributes
from yosai_intel_dashboard.src.services.configuration_service import DynamicConfigurationService
from yosai_intel_dashboard.src.services.door_mapping_service import DoorMappingService


def test_standardized_output(monkeypatch):
    dummy = DeviceAttributes(
        device_id="d1",
        device_name="Door 1",
        floor_number=1,
        security_level=5,
        is_entry=True,
        is_exit=False,
        is_elevator=False,
        is_stairwell=False,
        is_fire_escape=False,
        is_restricted=False,
        confidence=0.9,
        ai_reasoning="test",
    )

    def fake_generate(self, device_id, *args, **kwargs):
        return dummy

    monkeypatch.setattr(AIDeviceGenerator, "generate_device_attributes", fake_generate)
    service = DoorMappingService(DynamicConfigurationService())
    df = pd.DataFrame({"door_id": ["d1"]})
    result = service.process_uploaded_data(df)
    device = result["devices"][0]
    assert device["is_entry"] is True
    assert "entry" not in device


def test_registry_version(monkeypatch):
    dummy = DeviceAttributes(
        device_id="d1",
        device_name="Door 1",
        floor_number=1,
        security_level=5,
        is_entry=True,
        is_exit=False,
        is_elevator=False,
        is_stairwell=False,
        is_fire_escape=False,
        is_restricted=False,
        confidence=0.9,
        ai_reasoning="test",
    )

    class DummyRegistry:
        def get_active_version(
            self, model_name: str, default: str | None = None
        ) -> str:
            return "registry-v1"

    def fake_generate(self, device_id, *args, **kwargs):
        return dummy

    monkeypatch.setattr(AIDeviceGenerator, "generate_device_attributes", fake_generate)
    service = DoorMappingService(
        DynamicConfigurationService(), model_registry=DummyRegistry()
    )
    df = pd.DataFrame({"door_id": ["d1"]})
    result = service.process_uploaded_data(df)
    assert result["metadata"]["ai_model_version"] == "registry-v1"


def test_registry_fallback(monkeypatch):
    dummy = DeviceAttributes(
        device_id="d1",
        device_name="Door 1",
        floor_number=1,
        security_level=5,
        is_entry=True,
        is_exit=False,
        is_elevator=False,
        is_stairwell=False,
        is_fire_escape=False,
        is_restricted=False,
        confidence=0.9,
        ai_reasoning="test",
    )

    class DummyRegistry:
        def get_active_version(
            self, model_name: str, default: str | None = None
        ) -> str:
            return default

    def fake_generate(self, device_id, *args, **kwargs):
        return dummy

    monkeypatch.setattr(AIDeviceGenerator, "generate_device_attributes", fake_generate)
    service = DoorMappingService(
        DynamicConfigurationService(),
        model_registry=DummyRegistry(),
        fallback_version="fallback",
    )
    df = pd.DataFrame({"door_id": ["d1"]})
    result = service.process_uploaded_data(df)
    assert result["metadata"]["ai_model_version"] == "fallback"
