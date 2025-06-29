import pandas as pd
import json
from services.analytics_service import AnalyticsService
from services.file_processor import FileProcessor


def test_load_fixed_file_csv(tmp_path):
    csv = tmp_path / "data.csv"
    pd.DataFrame({"person_id": ["u1"], "door_id": ["d1"], "access_result": ["Granted"], "timestamp": ["2024-01-01"]}).to_csv(csv, index=False)
    processor = FileProcessor(upload_folder=str(tmp_path), allowed_extensions={"csv"})
    service = AnalyticsService()
    df = service._load_fixed_file(str(csv), processor)
    assert df is not None
    assert list(df.columns) == ["person_id", "door_id", "access_result", "timestamp"]


def test_load_fixed_file_json(tmp_path):
    json_path = tmp_path / "data.json"
    data = [{"person_id": "u1", "door_id": "d1", "access_result": "Granted", "timestamp": "2024-01-01"}]
    json_path.write_text(json.dumps(data))
    processor = FileProcessor(upload_folder=str(tmp_path), allowed_extensions={"json"})
    service = AnalyticsService()
    df = service._load_fixed_file(str(json_path), processor)
    assert df is not None
    assert "person_id" in df.columns


def test_summarize_fixed_data():
    service = AnalyticsService()
    df1 = pd.DataFrame({"person_id": ["u1"], "door_id": ["d1"], "timestamp": pd.to_datetime(["2024-01-01"]), "access_result": ["Granted"]})
    df2 = pd.DataFrame({"person_id": ["u2"], "door_id": ["d2"], "timestamp": pd.to_datetime(["2024-01-02"]), "access_result": ["Denied"]})
    summary = service._summarize_fixed_data([df1, df2])
    assert summary["status"] == "success"
    assert summary["total_events"] == 2
