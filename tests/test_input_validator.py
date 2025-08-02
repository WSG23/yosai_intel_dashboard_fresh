import sys
from types import SimpleNamespace

import pandas as pd
import pytest
from tests.import_helpers import safe_import, import_optional

stub_dynamic_config = SimpleNamespace(
    security=SimpleNamespace(max_upload_mb=10),
    upload=SimpleNamespace(allowed_file_types=[".csv", ".json", ".xlsx", ".xls"]),
)
safe_import('config.dynamic_config', SimpleNamespace()
    dynamic_config=stub_dynamic_config
)

from validation.security_validator import SecurityValidator


def test_none_upload_rejected():
    validator = SecurityValidator()
    with pytest.raises(Exception):
        validator.validate_input("<script>", "field")


def test_empty_dataframe_rejected():
    validator = SecurityValidator()
    with pytest.raises(Exception):
        validator.validate_input("DROP TABLE users; --", "query")


def test_valid_dataframe_allowed():
    validator = SecurityValidator()
    res = validator.validate_input("safe", "field")
    assert res["valid"]
