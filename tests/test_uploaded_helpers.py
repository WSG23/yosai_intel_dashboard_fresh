import pandas as pd
from services.analytics_service import AnalyticsService


def test_load_uploaded_data(monkeypatch):
    sample = {"file.csv": pd.DataFrame({"A": [1]})}
    monkeypatch.setattr(
        "pages.file_upload.get_uploaded_data", lambda: sample, raising=False
    )
    service = AnalyticsService()
    assert service.load_uploaded_data() == sample


def test_clean_uploaded_dataframe():
    df = pd.DataFrame({
        "Timestamp": ["2024-01-01 00:00:00"],
        "Person ID": ["u1"],
        "Token ID": ["t1"],
        "Device name": ["d1"],
        "Access result": ["Granted"],
    })
    service = AnalyticsService()
    cleaned = service.clean_uploaded_dataframe(df)
    assert list(cleaned.columns) == ["timestamp", "person_id", "token_id", "door_id", "access_result"]
    assert pd.api.types.is_datetime64_any_dtype(cleaned["timestamp"])


def test_summarize_dataframe():
    df = pd.DataFrame({
        "person_id": ["u1", "u2"],
        "door_id": ["d1", "d2"],
        "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02"]),
        "access_result": ["Granted", "Denied"],
    })
    service = AnalyticsService()
    summary = service.summarize_dataframe(df)
    assert summary["total_events"] == 2
    assert summary["active_users"] == 2
    assert summary["active_doors"] == 2
    assert summary["date_range"]["start"] == "2024-01-01"
    assert summary["date_range"]["end"] == "2024-01-02"
