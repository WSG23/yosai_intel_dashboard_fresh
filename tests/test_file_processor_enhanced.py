import pandas as pd
from services.file_processor import FileProcessor


def test_enhanced_processor(tmp_path):
    df = pd.DataFrame(
        {
            "userid": ["EMP1", "EMP2"],
            "device name": ["Door1", "Door2"],
            "access result": ["Granted", "Denied"],
            "datetime": ["2024-01-01 10:00:00", "2024-01-01 11:00:00"],
        }
    )
    csv_path = tmp_path / "sample.csv"
    df.to_csv(csv_path, index=False)

    processor = FileProcessor(upload_folder=str(tmp_path), allowed_extensions={"csv"})

    df_loaded = pd.read_csv(csv_path)
    suggestions = processor.get_mapping_suggestions(df_loaded)
    assert suggestions["missing_mappings"] == []

    result = processor._validate_data(df_loaded)
    assert result["valid"] is True
    mapped_df = result.get("data")
    assert mapped_df is not None
    assert list(mapped_df.columns) == ["person_id", "door_id", "access_result", "timestamp"]

