import pandas as pd

from yosai_intel_dashboard.src.services.data_processing.file_processor import FileProcessor


def test_process_csv(tmp_path):
    df = pd.DataFrame(
        {
            "person_id": ["u1", "u2"],
            "door_id": ["d1", "d2"],
            "access_result": ["Granted", "Denied"],
            "timestamp": ["2024-01-01", "2024-01-02"],
        }
    )
    csv_path = tmp_path / "sample.csv"
    df.to_csv(csv_path, index=False)

    service = FileProcessor()
    combined, info, processed, total = service.process_files([str(csv_path)])

    assert processed == 1
    assert total == 2
    assert len(combined) == 2
    assert info and info[0].startswith("✅")
