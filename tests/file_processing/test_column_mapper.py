import pandas as pd
from pathlib import Path

from file_processing.column_mapper import map_columns
from core.callback_events import CallbackEvent
from analytics_core.callbacks.unified_callback_manager import CallbackManager


def test_exact_mapping(tmp_path: Path):
    df = pd.DataFrame({"person": [1], "door": ["d"]})
    mapping = {"person_id": ["person"], "door_id": ["door"]}
    out = map_columns(df, mapping)
    assert "person_id" in out.columns and "door_id" in out.columns


def test_fuzzy_mapping(tmp_path: Path):
    df = pd.DataFrame({"pers": [1], "dor": ["d"]})
    mapping = {"person_id": [], "door_id": []}
    controller = CallbackManager()
    events = []

    def track(source, data):
        events.append(data)

    controller.register_callback(CallbackEvent.SYSTEM_WARNING, track)
    out = map_columns(df, mapping, controller=controller)
    assert "person_id" in out.columns
    assert events
