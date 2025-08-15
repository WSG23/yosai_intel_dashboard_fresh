import pandas as pd

from yosai_intel_dashboard.src.services.analytics.chunked_analytics_controller import ChunkedAnalyticsController


def test_process_chunk_flexible_detection():
    df = pd.DataFrame(
        {
            "Person ID": ["u1", "u2"],
            "Device name": ["d1", "d2"],
            "Access result": ["Granted", "Denied"],
        }
    )
    controller = ChunkedAnalyticsController(chunk_size=2)
    result = controller._process_chunk(df, [])
    assert result["unique_users"] == {"u1", "u2"}
    assert result["unique_doors"] == {"d1", "d2"}
    assert result["successful_events"] == 1
    assert result["failed_events"] == 1


def test_sets_aggregated_and_finalized():
    df = pd.DataFrame(
        {
            "Person ID": ["u1", "u2", "u1"],
            "Device name": ["d1", "d1", "d2"],
            "Access result": ["Granted", "Denied", "Granted"],
            "Timestamp": ["2024-01-01", "2024-01-02", "2024-01-03"],
        }
    )
    controller = ChunkedAnalyticsController(chunk_size=1)
    result = controller.process_large_dataframe(df, [])
    assert result["unique_users"] == 2
    assert result["unique_doors"] == 2
    assert result["successful_events"] == 2
    assert result["failed_events"] == 1
