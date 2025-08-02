import pandas as pd

from services.analytics.chunked_analytics_controller import ChunkedAnalyticsController


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
    assert result["date_range"]["start"] == "2024-01-01 10:00:00"
    assert result["date_range"]["end"] == "2024-01-01 10:00:00"
