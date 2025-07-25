import pytest

from yosai_intel_dashboard.src.services.ai_device_generator import AIDeviceGenerator, DeviceAttributes
from yosai_intel_dashboard.src.services.ai_mapping_store import ai_mapping_store
from yosai_intel_dashboard.src.services.upload import analyze_device_name_with_ai


class DummyAttrs:
    def __init__(self):
        self.floor_number = 3
        self.security_level = 4
        self.confidence = 0.7
        self.is_entry = False
        self.is_exit = True
        self.is_elevator = False
        self.is_stairwell = False
        self.is_fire_escape = True
        self.device_name = "Dummy"
        self.ai_reasoning = "dummy"


def test_learned_mapping_priority(monkeypatch):
    """Ensure learned mappings are used before invoking AI"""
    ai_mapping_store.clear()
    ai_mapping_store.set(
        "door_1",
        {
            "floor_number": 2,
            "security_level": 7,
            "confidence": 0.95,
            "is_entry": True,
            "device_name": "Door 1",
        },
    )

    def fail_generate(self, *args, **kwargs):
        raise AssertionError("AI should not be called")

    monkeypatch.setattr(AIDeviceGenerator, "generate_device_attributes", fail_generate)

    result = analyze_device_name_with_ai("door_1")
    assert result["floor_number"] == 2
    assert result["security_level"] == 7
    assert result["is_entry"] is True
    assert result["device_name"] == "Door 1"


def test_fallback_to_ai(monkeypatch):
    """If no learned mapping exists, AI generator should be used"""
    ai_mapping_store.clear()

    def fake_generate(self, name):
        return DummyAttrs()

    monkeypatch.setattr(AIDeviceGenerator, "generate_device_attributes", fake_generate)

    result = analyze_device_name_with_ai("unknown_door")
    assert result["floor_number"] == 3
    assert result["is_exit"] is True
