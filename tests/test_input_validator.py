import pandas as pd

from validation.security_validator import SecurityValidator


def test_none_upload_rejected():
    validator = SecurityValidator()
    res = validator.validate_file_upload(None)
    assert not res.valid


def test_empty_dataframe_rejected():
    validator = SecurityValidator()
    df = pd.DataFrame()
    res = validator.validate_file_upload(df)
    assert not res.valid


def test_valid_dataframe_allowed():
    validator = SecurityValidator()
    df = pd.DataFrame({"a": [1, 2]})
    res = validator.validate_file_upload(df)
    assert res.valid
