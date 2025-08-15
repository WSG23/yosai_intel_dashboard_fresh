import base64
from pathlib import Path
from typing import Any, Dict, Iterable

import pandas as pd


class DataFrameBuilder:
    """Fluent helper for constructing ``pandas`` DataFrames in tests."""

    def __init__(self, data: Dict[str, Iterable[Any]] | None = None) -> None:
        self._data: Dict[str, list[Any]] = {k: list(v) for k, v in (data or {}).items()}

    def add_column(self, name: str, values: Iterable[Any]) -> "DataFrameBuilder":
        self._data[name] = list(values)
        return self

    def build(self) -> pd.DataFrame:
        return pd.DataFrame(self._data)


class UploadFileBuilder:
    """Utility for creating upload-like file content."""

    def __init__(self, filename: str = "sample.csv") -> None:
        self.filename = filename
        self._df = pd.DataFrame()

    def with_filename(self, name: str) -> "UploadFileBuilder":
        self.filename = name
        return self

    def with_dataframe(self, df: pd.DataFrame) -> "UploadFileBuilder":
        self._df = df
        return self

    def as_base64(self) -> str:
        csv_bytes = self._df.to_csv(index=False).encode()
        encoded = base64.b64encode(csv_bytes).decode()
        return f"data:text/csv;base64,{encoded}"

    def write_csv(self, path: Path) -> Path:
        self._df.to_csv(path, index=False)
        return path
