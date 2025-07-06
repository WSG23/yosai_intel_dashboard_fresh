"""Helpers for preparing uploaded data for analytics."""

from __future__ import annotations

import pandas as pd

from services.data_validation import DataValidationService
from utils.mapping_helpers import map_and_clean


def prepare_dataframe(df: pd.DataFrame, validator: DataValidationService | None = None) -> pd.DataFrame:
    """Validate and clean ``df`` for analytics."""
    validator = validator or DataValidationService()
    df = validator.validate(df)
    return map_and_clean(df)

__all__ = ["prepare_dataframe"]
