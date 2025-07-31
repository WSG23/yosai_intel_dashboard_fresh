"""Upload data service protocol definitions."""

from __future__ import annotations

from typing import Any, Dict, List, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class UploadDataServiceProtocol(Protocol):
    """Interface for accessing uploaded data."""

    def get_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Return all uploaded dataframes."""
        ...

    def get_uploaded_filenames(self) -> List[str]:
        """Return names of uploaded files."""
        ...

    def clear_uploaded_data(self) -> None:
        """Remove all uploaded data."""
        ...

    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        """Return info dictionary for uploaded files."""
        ...

    def load_dataframe(self, filename: str) -> pd.DataFrame:
        """Load a specific uploaded dataframe."""
        ...

    def save_column_mappings(self, file_id: str, mappings: Dict[str, str]) -> None:
        """Persist column mappings for a file."""
        ...

    def save_device_mappings(self, file_id: str, mappings: Dict[str, Any]) -> None:
        """Persist device mappings for a file."""
        ...


__all__ = ["UploadDataServiceProtocol"]
