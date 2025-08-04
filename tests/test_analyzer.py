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

from yosai_intel_dashboard.src.services.analytics.processing.analyzer import Analyzer  # noqa: E402


def test_analyze():
    df = pd.DataFrame({"user": ["u1", "u1"], "device": ["d1", "d2"]})
    analyzer = Analyzer()
    res = analyzer.analyze(df, len(df))
    assert res["data_summary"]["total_records"] == 2
