from __future__ import annotations

from datetime import datetime, timedelta
import importlib.util
import random
from pathlib import Path
import types

module_path = (
    Path(__file__).resolve().parents[2]
    / "yosai_intel_dashboard"
    / "src"
    / "utils"
    / "sample_data_generator.py"
)
spec = importlib.util.spec_from_file_location("sample_data_generator", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # type: ignore[arg-type]

# Provide a minimal numpy substitute with deterministic choice
module.np = types.SimpleNamespace(
    random=types.SimpleNamespace(choice=lambda seq, p=None: seq[0])
)


def test_random_timestamp_within_range() -> None:
    start = datetime(2024, 1, 1)
    end = start + timedelta(days=1)
    random.seed(0)
    ts = module._random_timestamp(start, end)  # type: ignore[attr-defined]
    assert start <= ts <= end


def test_create_access_event_structure() -> None:
    start = datetime(2024, 1, 1)
    end = start + timedelta(days=1)
    random.seed(0)
    event = module._create_access_event(  # type: ignore[attr-defined]
        start,
        end,
        ["EMP0001"],
        ["VIS001"],
        ["MAIN_ENTRANCE"],
        ["Granted", "Denied", "Timeout", "Error"],
        [0.8, 0.15, 0.03, 0.02],
    )
    expected_keys = {
        "event_id",
        "timestamp",
        "person_id",
        "door_id",
        "badge_id",
        "access_result",
        "badge_status",
        "door_held_open_time",
        "entry_without_badge",
        "device_status",
    }
    assert set(event) == expected_keys
    assert event["door_id"] == "MAIN_ENTRANCE"
    assert event["access_result"] == "Granted"
