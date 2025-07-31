import sys
import types
from pathlib import Path

import pandas as pd
import pytest

try:
    import flask  # noqa: F401
except Exception:
    pytest.skip("flask not available", allow_module_level=True)

services_stub = types.ModuleType("services")
services_stub.__path__ = [str(Path(__file__).resolve().parents[1] / "services")]
sys.modules["services"] = services_stub

from yosai_intel_dashboard.src.services.analytics.data.transformer import DataTransformer  # noqa: E402


def test_transformer_basic():
    df = pd.DataFrame({"a": [1, 2]})
    t = DataTransformer()
    assert t.transform(df).equals(df)
    summary = t.summarize(df)
    assert summary["rows"] == 2
    assert "a" in summary["columns"]
