from pathlib import Path

import pandas as pd

from core.callback_events import CallbackEvent
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.file_processing.column_mapper import map_columns


def test_exact_mapping(tmp_path: Path):
    df = pd.DataFrame({"person": [1], "door": ["d"]})
    mapping = {"person_id": ["person"], "door_id": ["door"]}
    out = map_columns(df, mapping)
    assert "person_id" in out.columns and "door_id" in out.columns


def test_fuzzy_mapping(tmp_path: Path):
    df = pd.DataFrame({"pers": [1], "dor": ["d"]})
    mapping = {"person_id": [], "door_id": []}
    controller = TrulyUnifiedCallbacks()
    events = []

    def track(source, data):
        events.append(data)

    controller.register_callback(CallbackEvent.SYSTEM_WARNING, track)
    out = map_columns(df, mapping, controller=controller)
    assert "person_id" in out.columns
    assert events
