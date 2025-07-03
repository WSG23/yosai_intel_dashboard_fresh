import pandas as pd
from services.input_validator import InputValidator


def test_none_upload_rejected():
    validator = InputValidator(max_size_mb=1)
    res = validator.validate_file_upload(None)
    assert not res.valid


def test_empty_dataframe_rejected():
    validator = InputValidator(max_size_mb=1)
    df = pd.DataFrame()
    res = validator.validate_file_upload(df)
    assert not res.valid


def test_valid_dataframe_allowed():
    validator = InputValidator(max_size_mb=1)
    df = pd.DataFrame({"a": [1, 2]})
    res = validator.validate_file_upload(df)
    assert res.valid
