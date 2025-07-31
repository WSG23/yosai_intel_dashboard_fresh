import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SPEC_PATH = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "data_enhancer"
    / "mapping_utils.py"
)
spec = importlib.util.spec_from_file_location("mapping_utils", SPEC_PATH)
mapping_utils = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mapping_utils)
apply_fuzzy_column_matching = mapping_utils.apply_fuzzy_column_matching
apply_manual_mapping = mapping_utils.apply_manual_mapping
get_mapping_suggestions = mapping_utils.get_mapping_suggestions
get_ai_column_suggestions = mapping_utils.get_ai_column_suggestions


def test_apply_fuzzy_column_matching():
    df = pd.DataFrame(
        {
            "Person ID": ["p1"],
            "Door Name": ["d1"],
            "Result": ["granted"],
            "Time": ["2024-01-01"],
        }
    )
    renamed, mapping = apply_fuzzy_column_matching(
        df, ["person_id", "door_id", "access_result", "timestamp"]
    )
    assert list(renamed.columns) == [
        "person_id",
        "door_id",
        "access_result",
        "timestamp",
    ]
    assert mapping == {
        "person_id": "Person ID",
        "door_id": "Door Name",
        "access_result": "Result",
        "timestamp": "Time",
    }


def test_apply_manual_mapping_error():
    df = pd.DataFrame({"A": [1]})
    with pytest.raises(ValueError):
        apply_manual_mapping(df, {"person_id": "B"})


def test_get_mapping_suggestions():
    df = pd.DataFrame(
        {"UserID": ["u1"], "Door": ["d"], "Status": ["ok"], "Date": ["2023"]}
    )
    info = get_mapping_suggestions(df)
    assert set(info["required_columns"]) == {
        "person_id",
        "door_id",
        "access_result",
        "timestamp",
    }
    assert info["missing_mappings"] == []


def test_get_ai_column_suggestions():
    cols = ["PersonName", "DoorLocation", "TimeStamp", "ResultStatus", "BadgeID"]
    suggestions = get_ai_column_suggestions(cols)
    assert suggestions["PersonName"]["field"] == "person_id"
    assert suggestions["DoorLocation"]["field"] == "door_id"
    assert suggestions["TimeStamp"]["field"] == "timestamp"
    assert suggestions["ResultStatus"]["field"] == "access_result"
    assert suggestions["BadgeID"]["field"] == "token_id"
