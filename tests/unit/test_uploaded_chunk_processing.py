import pytest
try:
    from yosai_intel_dashboard.src.services import AnalyticsService
except Exception:  # pragma: no cover - skip if dependencies missing
    pytest.skip("analytics dependencies missing", allow_module_level=True)
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder


def test_process_uploaded_data_directly_chunked(tmp_path):
    df1 = (
        DataFrameBuilder()
        .add_column("Timestamp", ["2024-01-01 10:00:00", "2024-01-01 11:00:00"])
        .add_column("Person ID", ["u1", "u2"])
        .add_column("Token ID", ["t1", "t2"])
        .add_column("Device name", ["d1", "d1"])
        .add_column("Access result", ["Granted", "Denied"])
        .build()
    )
    df2 = (
        DataFrameBuilder()
        .add_column("Timestamp", ["2024-01-02 09:00:00"])
        .add_column("Person ID", ["u1"])
        .add_column("Token ID", ["t1"])
        .add_column("Device name", ["d2"])
        .add_column("Access result", ["Granted"])
        .build()
    )
    path1 = UploadFileBuilder().with_dataframe(df1).write_csv(tmp_path / "f1.csv")
    path2 = UploadFileBuilder().with_dataframe(df2).write_csv(tmp_path / "f2.csv")

    service = AnalyticsService()
    result = service._process_uploaded_data_directly({"f1.csv": path1, "f2.csv": path2})

    assert result["total_events"] == 3
    assert result["active_users"] == 2
    assert result["active_doors"] == 2
    assert result["date_range"]["start"] == "2024-01-01T00:00:00+00:00"
    assert result["date_range"]["end"] == "2024-01-02T00:00:00+00:00"
