import importlib.util
import sys
from pathlib import Path

import pandas as pd

from yosai_intel_dashboard.src.services.mapping.models import load_rules

spec = importlib.util.spec_from_file_location(
    "ai_column_mapper",
    Path(__file__).resolve().parents[1] / "utils" / "ai_column_mapper.py",
)
ai_module = importlib.util.module_from_spec(spec)

# Provide a minimal stub for the optional components dependency
sys.modules.setdefault(
    "components.plugin_adapter",
    importlib.util.module_from_spec(
        importlib.util.spec_from_loader("components.plugin_adapter", loader=None)
    ),
)
setattr(sys.modules["components.plugin_adapter"], "ComponentPluginAdapter", object)

spec.loader.exec_module(ai_module)
AIColumnMapperAdapter = ai_module.AIColumnMapperAdapter


class DummyAdapter:
    def __init__(self, mapping):
        self._mapping = mapping

    def suggest_columns(self, columns):
        return {c: self._mapping.get(c, "") for c in columns}


def test_map_and_standardize():
    df = pd.DataFrame({"RawA": [1], "RawB": [2]})

    dummy = DummyAdapter({"RawA": "Person ID", "RawB": "ドア名"})
    adapter = AIColumnMapperAdapter(dummy, use_japanese=True, rules=load_rules())

    out = adapter.map_and_standardize(df)
    assert list(out.columns) == ["person_id", "door_id"]
