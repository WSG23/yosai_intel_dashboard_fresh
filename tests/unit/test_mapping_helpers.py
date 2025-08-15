import pandas as pd

from yosai_intel_dashboard.src.utils.mapping_helpers import map_and_clean, standardize_column_names


def test_map_and_clean_basic():
    df = pd.DataFrame(
        {
            "Timestamp": ["2024-01-01 00:00:00"],
            "Person ID": [" u1 "],
            "Token ID": ["t1"],
            "Device name": ["d1"],
            "Access result": ["Granted"],
        }
    )

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
    df = pd.DataFrame(
        {
            "Timestamp": ["2024-01-01"],
            "Person ID": ["u1"],
        }
    )
    cleaned = map_and_clean(df)
    assert "token_id" not in cleaned.columns
    assert "door_id" not in cleaned.columns


def test_map_and_clean_with_learned_mappings():
    df = pd.DataFrame(
        {
            "Time": ["2024-01-01 12:00:00"],
            "User": [" u2 "],
            "Door": ["d2"],
            "Token ID": ["t2"],
        }
    )

    learned = {"Time": "timestamp", "User": "person_id", "Door": "door_id"}
    cleaned = map_and_clean(df, learned)

    assert list(cleaned.columns) == [
        "timestamp",
        "person_id",
        "door_id",
        "token_id",
    ]
    assert cleaned.loc[0, "person_id"] == "u2"


def test_standardize_column_names_basic():
    df = pd.DataFrame({"A B": [1], "C-D": [2], "e": [3]})
    out = standardize_column_names(df)
    assert list(out.columns) == ["a_b", "c_d", "e"]
