import pandas as pd
import sys
import types

import tests.stubs.flask as flask_stub

flask_stub.request = types.SimpleNamespace(path="/")
flask_stub.url_for = lambda *a, **k: "/"
sys.modules["flask"] = flask_stub

from utils.ai_column_mapper import standardize_column_names


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
