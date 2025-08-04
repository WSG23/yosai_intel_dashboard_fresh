import sys
import types
from pathlib import Path

import pandas as pd
import pytest
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

try:
    import flask  # noqa: F401
except Exception:
    pytest.skip("flask not available", allow_module_level=True)

services_stub = types.ModuleType("services")
services_stub.__path__ = [str(Path(__file__).resolve().parents[1] / "services")]
safe_import('services', services_stub)

from yosai_intel_dashboard.src.services.analytics.processing.aggregator import Aggregator  # noqa: E402


def test_aggregate():
    df = pd.DataFrame({"g": ["a", "a", "b"], "x": [1, 2, 3]})
    agg = Aggregator()
    result = agg.aggregate(df, ["g"], ["x"])
    assert set(result["g"]) == {"a", "b"}
