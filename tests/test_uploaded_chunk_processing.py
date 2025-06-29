import pandas as pd
from services.analytics_service import AnalyticsService


def test_process_uploaded_data_directly_chunked(tmp_path):
    df1 = pd.DataFrame({
        "Timestamp": ["2024-01-01 10:00:00", "2024-01-01 11:00:00"],
        "Person ID": ["u1", "u2"],
        "Token ID": ["t1", "t2"],
        "Device name": ["d1", "d1"],
        "Access result": ["Granted", "Denied"],
    })
    df2 = pd.DataFrame({
        "Timestamp": ["2024-01-02 09:00:00"],
        "Person ID": ["u1"],
        "Token ID": ["t1"],
        "Device name": ["d2"],
        "Access result": ["Granted"],
    })
    path1 = tmp_path / "f1.csv"
    path2 = tmp_path / "f2.csv"
    df1.to_csv(path1, index=False)
    df2.to_csv(path2, index=False)

    service = AnalyticsService()
    result = service._process_uploaded_data_directly({"f1.csv": path1, "f2.csv": path2})

    assert result["total_events"] == 3
    assert result["active_users"] == 2
    assert result["active_doors"] == 2
    assert result["date_range"]["start"] == "2024-01-01"
    assert result["date_range"]["end"] == "2024-01-02"
