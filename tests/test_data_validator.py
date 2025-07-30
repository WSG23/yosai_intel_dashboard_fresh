import pandas as pd

from validation.data_validator import DataValidator


def test_data_validator_missing_cols():
    df = pd.DataFrame({"a": [1]})
    validator = DataValidator(required_columns=["a", "b"])
    result = validator.validate_dataframe(df)
    assert not result.valid
    assert "missing_columns" in result.issues[0]


def test_data_validator_empty_df():
    df = pd.DataFrame()
    validator = DataValidator()
    result = validator.validate_dataframe(df)
    assert not result.valid
    assert "empty_dataframe" in result.issues


def test_data_validator_suspicious_columns():
    df = pd.DataFrame({"=cmd": [1], "b": [2]})
    validator = DataValidator()
    result = validator.validate_dataframe(df)
    assert not result.valid
    assert any("suspicious_column_names" in issue for issue in result.issues)
