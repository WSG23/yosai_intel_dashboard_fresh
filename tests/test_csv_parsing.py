import base64

import pandas as pd
import pytest

from yosai_intel_dashboard.src.services.data_processing.unified_upload_validator import (
    UnifiedUploadValidator,
)


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

    processor = UnifiedUploadValidator()
    with open(csv_path, "rb") as f:
        data_b64 = base64.b64encode(f.read()).decode()
    contents = f"data:text/csv;base64,{data_b64}"
    parsed = processor.validate_file(contents, "sample.csv")

    expected = df.copy()
    expected["timestamp"] = pd.to_datetime(expected["timestamp"])

    pd.testing.assert_frame_equal(parsed, expected)
