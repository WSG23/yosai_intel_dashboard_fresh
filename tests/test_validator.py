import types
import sys
from pathlib import Path

import pytest

try:
    import flask  # noqa: F401
except Exception:
    pytest.skip("flask not available", allow_module_level=True)

services_stub = types.ModuleType("services")
services_stub.__path__ = [str(Path(__file__).resolve().parents[1] / "services")]
sys.modules["services"] = services_stub

import pandas as pd
from services.analytics.data.validator import Validator  # noqa: E402


def test_validate_methods():
    val = Validator()
    assert val.validate_input("ok") == {"valid": True, "sanitized": "ok"}
    assert val.validate_file_upload("a.txt", b"data")["valid"]
    df = pd.DataFrame({"a": [1]})
    assert val.validate_dataframe(df).equals(df)
