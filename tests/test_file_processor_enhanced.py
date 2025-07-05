import pandas as pd
import base64

from services.data_processing.file_handler import FileHandler
from services.data_processing import process_file
from config.dynamic_config import dynamic_config


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

    processor = FileHandler()

    df_loaded = pd.read_csv(csv_path)
    suggestions = processor.get_mapping_suggestions(df_loaded)
    assert suggestions["missing_mappings"] == []

    result = processor._validate_data(df_loaded)
    assert result["valid"] is True
    mapped_df = result.get("data")
    assert mapped_df is not None
    assert list(mapped_df.columns) == [
        "person_id",
        "door_id",
        "access_result",
        "timestamp",
    ]


def test_malicious_filename_rejected(tmp_path):
    data = base64.b64encode(b"id,name\n1,A").decode()
    contents = f"data:text/csv;base64,{data}"
    result = process_file(contents, "../../evil.csv")
    assert result["success"] is False


def test_oversized_file_rejected(tmp_path):
    max_bytes = dynamic_config.security.max_upload_mb * 1024 * 1024
    data = base64.b64encode(b"A" * (max_bytes + 1)).decode()
    contents = f"data:text/csv;base64,{data}"
    result = process_file(contents, "big.csv")
    assert result["success"] is False


def test_upload_limit_allows_large_files():
    """Default upload size should permit files of at least 50MB."""
    assert dynamic_config.security.max_upload_mb >= 50
