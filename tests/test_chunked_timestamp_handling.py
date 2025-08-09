import pandas as pd
import pytest

try:
    from yosai_intel_dashboard.src.services.analytics.chunked_analytics_controller import ChunkedAnalyticsController
except Exception:  # pragma: no cover - skip if dependencies missing
    pytest.skip("analytics dependencies missing", allow_module_level=True)


def test_chunked_controller_handles_bad_timestamps():
    df = pd.DataFrame(
        {
            "person_id": ["u1", "u2"],
            "door_id": ["d1", "d2"],
            "access_result": ["Granted", "Denied"],
            "timestamp": ["2024-01-01 10:00:00", "bad-data"],
        }
    )

    controller = ChunkedAnalyticsController(chunk_size=1)
    result = controller.process_large_dataframe(df, ["trends", "anomaly"])

    assert result["rows_processed"] == len(df)
    assert result["date_range"]["start"] == "2024-01-01T10:00:00+00:00"
    assert result["date_range"]["end"] == "2024-01-01T10:00:00+00:00"
