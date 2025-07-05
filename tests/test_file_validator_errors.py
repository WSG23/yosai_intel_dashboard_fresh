from services.data_processing.unified_file_validator import (
    safe_decode_file,
    process_dataframe,
)


def test_safe_decode_file_invalid_base64():
    malformed = "data:text/csv;base64,@@@"
    assert safe_decode_file(malformed) is None


def test_process_dataframe_unsupported_type(tmp_path):
    data = b"col1,col2\n1,2"
    df, err = process_dataframe(data, "data.txt")
    assert df is None
    assert "Unsupported file type" in err


def test_process_dataframe_invalid_json():
    bad_json = b"{invalid"  # not valid JSON
    df, err = process_dataframe(bad_json, "file.json")
    assert df is None
    assert err is not None
    assert "Error processing file" in err
