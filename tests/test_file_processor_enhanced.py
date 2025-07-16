import base64
import pandas as pd

from tests.utils.builders import DataFrameBuilder, UploadFileBuilder

from tests.fake_configuration import FakeConfiguration

fake_cfg = FakeConfiguration()
from services.data_enhancer import (
    apply_fuzzy_column_matching,
    get_mapping_suggestions,
)
from services.data_processing.file_processor import process_uploaded_file
from services.data_processing.unified_upload_validator import UnifiedUploadValidator
from core.security_validator import SecurityValidator


def test_enhanced_processor(tmp_path):
    df = (
        DataFrameBuilder()
        .add_column("userid", ["EMP1", "EMP2"])
        .add_column("device name", ["Door1", "Door2"])
        .add_column("access result", ["Granted", "Denied"])
        .add_column("datetime", ["2024-01-01 10:00:00", "2024-01-01 11:00:00"])
        .build()
    )
    csv_path = tmp_path / "sample.csv"
    df.to_csv(csv_path, index=False)

    processor = UnifiedUploadValidator()

    df_loaded = pd.read_csv(csv_path)
    suggestions = get_mapping_suggestions(df_loaded)
    assert suggestions["missing_mappings"] == []

    mapped_df, _ = apply_fuzzy_column_matching(
        df_loaded, ["person_id", "door_id", "access_result", "timestamp"]
    )
    validator = SecurityValidator()
    csv_bytes = mapped_df.to_csv(index=False).encode("utf-8")
    result = validator.validate_file_upload("sample.csv", csv_bytes)
    assert result["valid"] is True


def test_malicious_filename_rejected(tmp_path):
    contents = (
        UploadFileBuilder()
        .with_dataframe(
            DataFrameBuilder().add_column("id", [1]).add_column("name", ["A"]).build()
        )
        .as_base64()
    )
    result = process_uploaded_file(contents, "../../evil.csv", config=fake_cfg)
    assert result["success"] is False


def test_oversized_file_rejected(tmp_path):
    max_bytes = fake_cfg.security.max_upload_mb * 1024 * 1024
    data = base64.b64encode(b"A" * (max_bytes + 1)).decode()
    contents = f"data:text/csv;base64,{data}"
    result = process_uploaded_file(contents, "big.csv", config=fake_cfg)
    assert result["success"] is False


def test_upload_limit_allows_large_files():
    """Default upload size should permit files of at least 50MB."""
    assert fake_cfg.security.max_upload_mb >= 50
