import pandas as pd
import sys
import types

import tests.stubs.flask as flask_stub

flask_stub.request = types.SimpleNamespace(path="/")
flask_stub.url_for = lambda *a, **k: "/"
sys.modules["flask"] = flask_stub

from utils.ai_column_mapper import AIColumnMapperAdapter


class DummyAdapter:
    def __init__(self, mapping):
        self._mapping = mapping

    def suggest_columns(self, columns):
        return {c: self._mapping.get(c, "") for c in columns}


def test_map_and_standardize(monkeypatch):
    df = pd.DataFrame({"RawA": [1], "RawB": [2]})

    dummy = DummyAdapter({"RawA": "Person ID", "RawB": "ドア名"})
    adapter = AIColumnMapperAdapter(dummy)

    out = adapter.map_and_standardize(df)
    assert list(out.columns) == ["person_id", "door_id"]
