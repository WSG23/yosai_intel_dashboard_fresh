"""Persistent uploaded data store module."""
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class UploadedDataStore:
    """Persistent uploaded data store with file system backup.

    The class is designed to be thread-safe for concurrent writes. All
    modifying operations are guarded by an internal :class:`threading.Lock`.
    Reads return copies of the underlying structures and can run without
    holding the lock.
    """

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self._lock = threading.Lock()
        self._data_store: Dict[str, pd.DataFrame] = {}
        self._file_info_store: Dict[str, Dict[str, Any]] = {}
        self.storage_dir = Path(storage_dir or "temp/uploaded_data")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._load_from_disk()

    # -- Internal helpers ---------------------------------------------------
    def _get_file_path(self, filename: str) -> Path:
        safe_name = filename.replace(" ", "_").replace("/", "_")
        return self.storage_dir / f"{safe_name}.pkl"

    def _info_path(self) -> Path:
        return self.storage_dir / "file_info.json"

    def _load_from_disk(self) -> None:
        try:
            if self._info_path().exists():
                with open(self._info_path(), "r") as f:
                    self._file_info_store = json.load(f)
            for fname in self._file_info_store.keys():
                fpath = self._get_file_path(fname)
                if fpath.exists():
                    df = pd.read_pickle(fpath)
                    self._data_store[fname] = df
                    logger.info(f"Loaded {fname} from disk")
        except Exception as e:  # pragma: no cover - best effort
            logger.error(f"Error loading uploaded data: {e}")

    def _save_to_disk(self, filename: str, df: pd.DataFrame) -> None:
        with self._lock:
            try:
                df.to_pickle(self._get_file_path(filename))
                self._file_info_store[filename] = {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns),
                    "upload_time": datetime.now().isoformat(),
                    "size_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
                }
                with open(self._info_path(), "w") as f:
                    json.dump(self._file_info_store, f, indent=2)
            except Exception as e:  # pragma: no cover - best effort
                logger.error(f"Error saving uploaded data: {e}")

    # -- Public API ---------------------------------------------------------
    def add_file(self, filename: str, df: pd.DataFrame) -> None:
        with self._lock:
            self._data_store[filename] = df
        self._save_to_disk(filename, df)

    def get_all_data(self) -> Dict[str, pd.DataFrame]:
        return self._data_store.copy()

    def get_filenames(self) -> List[str]:
        return list(self._data_store.keys())

    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        return self._file_info_store.copy()

    def clear_all(self) -> None:
        with self._lock:
            self._data_store.clear()
            self._file_info_store.clear()
            try:
                for pkl in self.storage_dir.glob("*.pkl"):
                    pkl.unlink()
                if self._info_path().exists():
                    self._info_path().unlink()
            except Exception as e:  # pragma: no cover - best effort
                logger.error(f"Error clearing uploaded data: {e}")


# Global persistent storage instance
uploaded_data_store = UploadedDataStore()

__all__ = ["UploadedDataStore", "uploaded_data_store"]
