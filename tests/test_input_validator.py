import pandas as pd
from core.unified_file_validator import UnifiedFileValidator as FileHandler



def test_none_upload_rejected():
    validator = UnifiedFileValidator(max_size_mb=1)
    res = validator.validate_file_upload(None)
    assert not res.valid


def test_empty_dataframe_rejected():
    validator = UnifiedFileValidator(max_size_mb=1)
    df = pd.DataFrame()
    res = validator.validate_file_upload(df)
    assert not res.valid


def test_valid_dataframe_allowed():
    validator = UnifiedFileValidator(max_size_mb=1)
    df = pd.DataFrame({"a": [1, 2]})
    res = validator.validate_file_upload(df)
    assert res.valid
