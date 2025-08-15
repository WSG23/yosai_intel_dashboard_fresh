import sys

# Ensure real pandas is used instead of stub
sys.modules.pop("pandas", None)
import pandas as pd


def test_inline_dataframe_schema():
    """Validate sample ML schema using an inline DataFrame."""
    df = pd.DataFrame(
        [
            {"event_id": 1, "timestamp": "2023-01-01", "value": 0.5},
            {"event_id": 2, "timestamp": "2023-01-02", "value": 1.2},
        ]
    )

    assert list(df.columns) == ["event_id", "timestamp", "value"]
    assert df.shape == (2, 3)
