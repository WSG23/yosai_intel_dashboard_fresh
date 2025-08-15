import pandas as pd

from yosai_intel_dashboard.src.utils.mapping_helpers import standardize_column_names


def test_standardize_mixed_language_columns():
    df = pd.DataFrame(columns=["Timestamp", "ユーザーID", "Token ID", "ドア名", "結果"])
    out = standardize_column_names(df)
    assert list(out.columns) == [
        "timestamp",
        "person_id",
        "token_id",
        "door_id",
        "access_result",
    ]
