import pandas as pd
from analytics.security_score_calculator import SecurityScoreCalculator
from services.data_processing.unified_upload_validator import validate_dataframe_content


def test_data_validator_missing_required_columns():
    df = pd.DataFrame({"timestamp": ["2024-01-01"]})
    valid, message = SecurityScoreCalculator().validate_dataframe(df)
    assert not valid
    assert "Missing required columns" in message


def test_dataframe_validation_flags_dangerous_column():
    df = pd.DataFrame({"=cmd": ["1"]})
    result = validate_dataframe_content(df)
    assert "suspicious_column_names" in result["issues"]
