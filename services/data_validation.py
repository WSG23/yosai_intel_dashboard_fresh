"""Wrapper service around DataFrameSecurityValidator."""

from typing import Any, Tuple

import pandas as pd
from security.dataframe_validator import DataFrameSecurityValidator


class DataValidationService:
    """Service providing DataFrame validation helpers."""

    def __init__(self) -> None:
        self._validator = DataFrameSecurityValidator()

    def __getattr__(self, item: str) -> Any:
        return getattr(self._validator, item)

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._validator.validate(df)

    def validate_for_upload(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._validator.validate_for_upload(df)

    def validate_for_analysis(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
        return self._validator.validate_for_analysis(df)

