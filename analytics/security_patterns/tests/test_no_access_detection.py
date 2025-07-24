import importlib.util
import sys
import types
from pathlib import Path

import pandas as pd

MODULE_DIR = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_no_access_detection_finds_denied_events(monkeypatch):
    # Stub minimal services and flask_caching packages required during imports
    services_mod = types.ModuleType("services")
    registry_mod = types.ModuleType("services.registry")
    registry_mod.get_service = lambda name: None
    services_mod.registry = registry_mod
    monkeypatch.setitem(sys.modules, "services", services_mod)
    monkeypatch.setitem(sys.modules, "services.registry", registry_mod)
    monkeypatch.setitem(sys.modules, "flask_caching", types.ModuleType("flask_caching"))

    data_prep = load_module("analytics.security_patterns.data_prep", MODULE_DIR / "data_prep.py")
    detector = load_module("analytics.security_patterns.no_access_detection", MODULE_DIR / "no_access_detection.py")

    df = pd.DataFrame([
        {"timestamp": "2024-01-01 10:00:00", "person_id": "u1", "door_id": "d1", "access_result": "Denied"},
        {"timestamp": "2024-01-01 10:05:00", "person_id": "u1", "door_id": "d1", "access_result": "Granted"},
    ])
    cleaned = data_prep.prepare_security_data(df)
    threats = detector.detect_no_access(cleaned)
    assert isinstance(threats, list)
    assert len(threats) > 0
