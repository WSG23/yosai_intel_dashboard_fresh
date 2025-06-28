import pandas as pd
from utils.mapping_helpers import map_and_clean


def test_map_and_clean_basic():
    df = pd.DataFrame({
        "Timestamp": ["2024-01-01 00:00:00"],
        "Person ID": [" u1 "],
        "Token ID": ["t1"],
        "Device name": ["d1"],
        "Access result": ["Granted"],
    })

    cleaned = map_and_clean(df)
    assert list(cleaned.columns) == [
        "timestamp",
        "person_id",
        "token_id",
        "door_id",
        "access_result",
    ]
    assert pd.api.types.is_datetime64_any_dtype(cleaned["timestamp"])
    assert cleaned.loc[0, "person_id"] == "u1"


def test_map_and_clean_missing_columns():
    df = pd.DataFrame({
        "Timestamp": ["2024-01-01"],
        "Person ID": ["u1"],
    })
    cleaned = map_and_clean(df)
    assert "token_id" not in cleaned.columns
    assert "door_id" not in cleaned.columns
