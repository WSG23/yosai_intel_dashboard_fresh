"""Helpers for preparing uploaded data for analytics."""

from __future__ import annotations

import pandas as pd

from utils.mapping_helpers import map_and_clean
from validation.security_validator import SecurityValidator


def prepare_dataframe(
    df: pd.DataFrame, validator: SecurityValidator | None = None
) -> pd.DataFrame:
    """Validate and clean ``df`` for analytics."""
    validator = validator or SecurityValidator()
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    validator.validate_file_upload("data.csv", csv_bytes)
    return map_and_clean(df)


__all__ = ["prepare_dataframe"]
