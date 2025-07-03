"""Data loading helpers for uploaded files."""

from pathlib import Path
from typing import Any, Iterator

import pandas as pd

from services.data_validation import DataValidationService
from utils.mapping_helpers import map_and_clean


class DataLoadingService:
    """Load and stream uploaded file data."""

    def __init__(self, validator: DataValidationService | None = None) -> None:
        self.validator = validator or DataValidationService()

    def load_dataframe(self, source: Any) -> pd.DataFrame:
        if isinstance(source, (str, Path)) or hasattr(source, "read"):
            df = pd.read_csv(source, encoding="utf-8")
        else:
            df = source
        df = self.validator.validate(df)
        return map_and_clean(df)

    def stream_file(
        self, source: Any, chunksize: int = 50000
    ) -> Iterator[pd.DataFrame]:
        if isinstance(source, (str, Path)) or hasattr(source, "read"):
            for chunk in pd.read_csv(source, chunksize=chunksize, encoding="utf-8"):
                chunk = self.validator.validate(chunk)
                yield map_and_clean(chunk)
        else:
            df = self.validator.validate(source)
            yield map_and_clean(df)
