import base64
import io
import sys
from types import SimpleNamespace

import pandas as pd
import pytest
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

stub_dynamic_config = SimpleNamespace(
    security=SimpleNamespace(max_upload_mb=10),
    upload=SimpleNamespace(allowed_file_types=[".csv", ".json", ".xlsx", ".xls"]),
)
safe_import('config.dynamic_config', SimpleNamespace()
    dynamic_config=stub_dynamic_config
)

from validation.security_validator import SecurityValidator


@pytest.mark.parametrize("sep", [";", "\t"])
def test_parse_csv_with_various_delimiters(tmp_path, sep):
    data = {
        "person_id": ["EMP1", "EMP2"],
        "door_id": ["D1", "D2"],
        "access_result": ["Granted", "Denied"],
        "timestamp": ["2024-01-01 10:00:00", "2024-01-01 11:00:00"],
    }
    df = pd.DataFrame(data)

    csv_path = tmp_path / "sample.csv"
    df.to_csv(csv_path, index=False, sep=sep)

    validator = SecurityValidator()
    assert validator.validate_input("ok")["valid"]
    with open(csv_path, "rb") as f:
        csv_bytes = f.read()

    contents = base64.b64encode(csv_bytes).decode()
    parsed = pd.read_csv(io.BytesIO(base64.b64decode(contents)), sep=sep)
    parsed["timestamp"] = pd.to_datetime(parsed["timestamp"])

    expected = df.copy()
    expected["timestamp"] = pd.to_datetime(expected["timestamp"])

    pd.testing.assert_frame_equal(parsed, expected)
