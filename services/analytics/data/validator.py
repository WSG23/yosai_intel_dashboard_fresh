from __future__ import annotations

"""Validation helper for analytics uploads."""

from typing import Dict

import pandas as pd

from validation.security_validator import SecurityValidator


class Validator:
    """Wrap :class:`SecurityValidator` for analytics pipelines."""

    def __init__(self, validator: SecurityValidator | None = None) -> None:
        self.validator = validator or SecurityValidator()

    def validate_input(self, value: str, field_name: str = "input") -> Dict[str, any]:
        return self.validator.validate_input(value, field_name)

    def validate_file_upload(self, filename: str, content: bytes) -> Dict[str, any]:
        return self.validator.validate_file_upload(filename, content)

    # dataframe level hook used in some pipelines
    def validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return df


__all__ = ["Validator"]
