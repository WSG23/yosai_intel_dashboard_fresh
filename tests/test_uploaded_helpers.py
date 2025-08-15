import pytest
try:
    from yosai_intel_dashboard.src.services.analytics.file_processing_utils import (
        aggregate_counts,
        calculate_date_range,
        stream_uploaded_file,
        update_counts,
        update_timestamp_range,
    )
    from yosai_intel_dashboard.src.services import AnalyticsService
except Exception:  # pragma: no cover - skip if dependencies missing
    pytest.skip("analytics dependencies missing", allow_module_level=True)
from tests.unit.fakes import FakeUploadDataService, FakeUploadStore
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder
import pandas as pd


def test_load_uploaded_data():
    sample = {"file.csv": DataFrameBuilder().add_column("A", [1]).build()}
    store = FakeUploadStore()
    for name, df in sample.items():
        store.add_file(name, df)
    data_service = FakeUploadDataService(store)
    service = AnalyticsService(upload_data_service=data_service)
    assert service.load_uploaded_data() == sample


def test_clean_uploaded_dataframe():
    df = (
        DataFrameBuilder()
        .add_column("Timestamp", ["2024-01-01 00:00:00"])
        .add_column("Person ID", ["u1"])
        .add_column("Token ID", ["t1"])
        .add_column("Device name", ["d1"])
        .add_column("Access result", ["Granted"])
        .build()
    )
    service = AnalyticsService()
    cleaned = service.clean_uploaded_dataframe(df)
    assert list(cleaned.columns) == [
        "timestamp",
        "person_id",
        "token_id",
        "door_id",
        "access_result",
    ]
    assert pd.api.types.is_datetime64_any_dtype(cleaned["timestamp"])


def test_summarize_dataframe():
    df = (
        DataFrameBuilder()
        .add_column("person_id", ["u1", "u2"])
        .add_column("door_id", ["d1", "d2"])
        .add_column("timestamp", pd.to_datetime(["2024-01-01", "2024-01-02"]))
        .add_column("access_result", ["Granted", "Denied"])
        .build()
    )
    service = AnalyticsService()
    summary = service.summarize_dataframe(df)
    assert summary["total_events"] == 2
    assert summary["active_users"] == 2
    assert summary["active_doors"] == 2
    assert summary["date_range"]["start"] == "2024-01-01T00:00:00+00:00"
    assert summary["date_range"]["end"] == "2024-01-02T00:00:00+00:00"
    assert summary["access_patterns"] == {"Granted": 1, "Denied": 1}
    assert summary["top_users"] == [
        {"user_id": "u1", "count": 1},
        {"user_id": "u2", "count": 1},
    ]
    assert summary["top_doors"] == [
        {"door_id": "d1", "count": 1},
        {"door_id": "d2", "count": 1},
    ]


def test_summarize_dataframe_handles_missing_columns_and_empty():
    df_missing = DataFrameBuilder().add_column("person_id", ["u1"]).build()
    service = AnalyticsService()
    missing = service.summarize_dataframe(df_missing)
    assert missing["active_doors"] == 0
    assert missing["access_patterns"] == {}
    assert missing["date_range"] == {"start": "Unknown", "end": "Unknown"}
    assert missing["top_doors"] == []

    empty = service.summarize_dataframe(pd.DataFrame())
    assert empty["total_events"] == 0
    assert empty["active_users"] == 0
    assert empty["top_users"] == []


def test_count_and_date_helpers():
    from collections import Counter

    df = (
        DataFrameBuilder()
        .add_column("person_id", ["u1", "u2", "u1"])
        .add_column("door_id", ["d1", "d1", "d2"])
        .add_column("timestamp", ["2024-01-01", "2024-01-03", "2024-01-02"])
        .build()
    )
    service = AnalyticsService()
    u_counts, d_counts = Counter(), Counter()
    update_counts(df, u_counts, d_counts)
    assert u_counts["u1"] == 2
    assert d_counts["d1"] == 2

    min_ts, max_ts = update_timestamp_range(df, None, None)
    dr = calculate_date_range(min_ts, max_ts)
    assert dr["start"] == "2024-01-01"
    assert dr["end"] == "2024-01-03"


def test_stream_uploaded_file(tmp_path):
    df = (
        DataFrameBuilder()
        .add_column("Timestamp", ["2024-01-01 10:00:00"])
        .add_column("Person ID", ["u1"])
        .add_column("Device name", ["d1"])
        .build()
    )
    path = UploadFileBuilder().with_dataframe(df).write_csv(tmp_path / "x.csv")
    service = AnalyticsService()
    chunks = list(stream_uploaded_file(service.data_loading_service, path, chunksize=1))
    assert len(chunks) == 1
    assert list(chunks[0].columns) == ["timestamp", "person_id", "door_id"]


def test_aggregate_counts():
    from collections import Counter

    df1 = (
        DataFrameBuilder()
        .add_column("person_id", ["u1", "u2"])
        .add_column("door_id", ["d1", "d2"])
        .add_column("timestamp", ["2024-01-01", "2024-01-02"])
        .build()
    )
    df2 = (
        DataFrameBuilder()
        .add_column("person_id", ["u1"])
        .add_column("door_id", ["d1"])
        .add_column("timestamp", ["2024-01-03"])
        .build()
    )

    service = AnalyticsService()
    u_counts, d_counts = Counter(), Counter()
    total, min_ts, max_ts = aggregate_counts([df1, df2], u_counts, d_counts, None, None)

    assert total == 3
    assert u_counts["u1"] == 2
    assert d_counts["d1"] == 2
    dr = calculate_date_range(min_ts, max_ts)
    assert dr["start"] == "2024-01-01"
    assert dr["end"] == "2024-01-03"
