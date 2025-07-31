import pandas as pd

from yosai_intel_dashboard.src.services.analytics_service import AnalyticsService


def test_analyze_with_chunking_large_df():
    df = pd.DataFrame(
        {
            "person_id": [f"user_{i}" for i in range(120000)],
            "door_id": [f"door_{i % 100}" for i in range(120000)],
            "access_result": [
                "Granted" if i % 2 == 0 else "Denied" for i in range(120000)
            ],
            "timestamp": pd.date_range("2024-01-01", periods=120000, freq="min"),
        }
    )

    service = AnalyticsService()
    result = service.analyze_with_chunking(
        df, ["security", "trends", "anomaly", "behavior"]
    )

    summary = result.get("processing_summary", {})
    assert summary.get("rows_processed") == len(df)
    assert summary.get("chunking_used") is True
