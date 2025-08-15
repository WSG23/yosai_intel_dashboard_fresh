import pandas as pd

from yosai_intel_dashboard.src.services.result_formatting import (
    apply_regular_analysis,
    prepare_regular_result,
)


def test_prepare_regular_result():
    df = pd.DataFrame({"a": [1, 2]})
    res = prepare_regular_result(df)
    assert res["total_events"] == 2
    assert res["columns"] == ["a"]
    assert res["processing_summary"]["chunking_used"] is False


def test_apply_regular_analysis():
    df = pd.DataFrame(
        {
            "person_id": ["u1", "u1", "u2"],
            "door_id": ["d1", "d1", "d2"],
            "access_result": ["Granted", "Denied", "Granted"],
            "timestamp": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"]),
        }
    )
    res = apply_regular_analysis(df, ["basic", "user"])
    assert "basic_stats" in res
    assert res["user_analysis"]["active_users"] == 2
