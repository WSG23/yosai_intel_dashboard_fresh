import pandas as pd
import base64
from services.data_processing import process_file


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

    data = base64.b64encode(csv_path.read_bytes()).decode()
    contents = f"data:text/csv;base64,{data}"
    result = process_file(contents, "sample.csv")
    df_loaded = result.get("data")

    assert result["success"] is True
    assert len(df_loaded) == 2
