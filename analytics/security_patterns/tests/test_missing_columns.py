import pandas as pd
import pytest

from analytics.security_patterns.multiple_attempts_detection import (
    detect_multiple_attempts,
)
from analytics.security_patterns.pattern_detection import detect_rapid_attempts
from analytics.security_patterns.tailgate_detection import detect_tailgate


@pytest.mark.parametrize("func", [detect_tailgate, detect_multiple_attempts, detect_rapid_attempts])
def test_missing_columns_return_empty(func, caplog):
    df = pd.DataFrame({"timestamp": ["2024-01-01"], "person_id": ["u1"]})
    with caplog.at_level("WARNING"):
        result = func(df)
    assert result == []
    assert any("Missing required columns" in r.getMessage() for r in caplog.records)
