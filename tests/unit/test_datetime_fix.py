import pandas as pd

from yosai_intel_dashboard.src.services.analytics.analytics_service import AnalyticsService
from yosai_intel_dashboard.src.services.result_formatting import ensure_datetime_columns


def create_test_data(rows=100):
    import random
    from datetime import datetime, timedelta

    data = []
    base_date = datetime(2024, 1, 1)
    for i in range(rows):
        data.append(
            {
                "person_id": f"USER_{(i % 150) + 1:03d}",
                "door_id": f"DOOR_{(i % 25) + 1:02d}",
                "access_result": random.choice(
                    ["Granted", "Granted", "Granted", "Denied"]
                ),
                "timestamp": (base_date + timedelta(minutes=i)).isoformat(),
                "badge_id": f"BADGE_{i % 200:04d}",
            }
        )
    return pd.DataFrame(data)


def test_ensure_datetime_columns():
    df = create_test_data(50)
    assert df["timestamp"].dtype == object
    df_fixed = ensure_datetime_columns(df)
    assert pd.api.types.is_datetime64_any_dtype(df_fixed["timestamp"])


def test_analyze_with_datetime_fix():
    df = create_test_data(100)
    service = AnalyticsService()
    result = service.analyze_with_chunking(df, ["basic"])
    summary = result.get("processing_summary", {})
    assert summary.get("rows_processed") == len(df)
