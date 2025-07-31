from __future__ import annotations

from typing import Dict

import pandas as pd

from yosai_intel_dashboard.src.utils.upload_store import UploadedDataStore


class Uploader:
    """Simple wrapper to save dataframes using :class:`UploadedDataStore`."""

    def __init__(self, store: UploadedDataStore) -> None:
        self.store = store

    def add_file(self, filename: str, df: pd.DataFrame) -> None:
        """Save ``df`` to ``filename`` using the underlying store."""
        self.store.add_file(filename, df)

    def get_all_data(self) -> Dict[str, pd.DataFrame]:
        """Return all uploaded data from the store."""
        return self.store.get_all_data()


__all__ = ["Uploader"]
