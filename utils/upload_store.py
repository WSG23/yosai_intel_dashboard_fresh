"""Persistent uploaded data store module."""

import asyncio
import json
import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

import pandas as pd

from config.app_config import UploadConfig
from core.cache_manager import CacheConfig, InMemoryCacheManager
from core.unicode import sanitize_dataframe
from services.upload.protocols import UploadStorageProtocol
from unicode_toolkit import safe_encode_text

_cache_manager = InMemoryCacheManager(CacheConfig())


class UploadStoreProtocol(Protocol):
    """Interface for uploaded data storage backends."""

    def add_file(self, filename: str, dataframe: pd.DataFrame) -> None: ...

    def get_all_data(self) -> Dict[str, pd.DataFrame]: ...

    def clear_all(self) -> None: ...

    def load_dataframe(self, filename: str) -> pd.DataFrame: ...

    def get_filenames(self) -> List[str]: ...

    def get_file_info(self) -> Dict[str, Dict[str, Any]]: ...

    def wait_for_pending_saves(self) -> None: ...


logger = logging.getLogger(__name__)


class UploadedDataStore(UploadStorageProtocol):
    """Persistent uploaded data store with file system backup.

    The class is designed to be thread-safe for concurrent writes. All
    modifying operations are guarded by an internal :class:`threading.Lock`.
    Reads return copies of the underlying structures and can run without
    holding the lock.
    """

    def __init__(
        self, storage_dir: Optional[Path] = None, *, config: UploadConfig | None = None
    ) -> None:
        self._lock = threading.Lock()
        self._data_store: Dict[str, pd.DataFrame] = {}
        self._file_info_store: Dict[str, Dict[str, Any]] = {}
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._save_futures: Dict[str, Future] = {}
        cfg = config or UploadConfig()
        self.storage_dir = Path(storage_dir or cfg.folder)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._load_info_from_disk()

    # -- Internal helpers ---------------------------------------------------
    def _get_file_path(self, filename: str) -> Path:
        """Return a sanitized path for the given ``filename``.

        Filenames may contain regular characters, spaces or forward slashes,
        which will be replaced by underscores. Any filename containing ``..``
        or a backslash is rejected with :class:`ValueError` to avoid directory
        traversal. The sanitized filename will be stored as ``<name>.parquet``
        inside :attr:`storage_dir`.
        """

        if ".." in filename or "\\" in filename:
            raise ValueError(f"Unsafe filename: {filename}")

        safe_name = filename.replace(" ", "_").replace("/", "_")
        return self.storage_dir / f"{safe_name}.parquet"

    def get_file_path(self, filename: str) -> Path:
        """Public wrapper for :meth:`_get_file_path`."""
        return self._get_file_path(filename)

    def _info_path(self) -> Path:
        return self.storage_dir / "file_info.json"

    def _load_info_from_disk(self) -> None:
        try:
            if self._info_path().exists():
                with open(
                    self._info_path(),
                    "r",
                    encoding="utf-8",
                    errors="replace",
                ) as f:
                    self._file_info_store = json.load(f)

            filenames = set(self._file_info_store.keys())
            # include any legacy pickle files not tracked yet
            for pkl_file in self.storage_dir.glob("*.pkl"):
                filenames.add(pkl_file.stem)
                self._file_info_store.setdefault(pkl_file.stem, {})

            modified = False
            for fname in filenames:
                fpath = self._get_file_path(fname)
                pkl_path = fpath.with_suffix(".pkl")
                if pkl_path.exists():
                    try:
                        df = pd.read_pickle(pkl_path)
                        df = sanitize_dataframe(df)
                        df.to_parquet(fpath, index=False)
                        try:
                            pkl_path.unlink()
                        except Exception:  # pragma: no cover - best effort
                            pass
                        self._file_info_store[fname] = {
                            **self._file_info_store.get(fname, {}),
                            "rows": len(df),
                            "columns": len(df.columns),
                            "path": str(fpath),
                            "upload_time": datetime.now().isoformat(),
                            "size_mb": round(
                                df.memory_usage(deep=True).sum() / 1024 / 1024, 2
                            ),
                        }
                        modified = True
                    except Exception as exc:  # pragma: no cover - best effort
                        logger.error(f"Error converting {pkl_path}: {exc}")
                        continue
                else:
                    # Ensure path metadata exists for already-converted files
                    if "path" not in self._file_info_store.get(fname, {}):
                        self._file_info_store[fname]["path"] = str(fpath)
            if modified:
                with open(self._info_path(), "w", encoding="utf-8") as f:
                    json.dump(self._file_info_store, f, indent=2)
        except Exception as e:  # pragma: no cover - best effort
            logger.error(f"Error loading uploaded data info: {e}")

    def _save_to_disk(self, filename: str, df: pd.DataFrame) -> None:
        try:
            path = self._get_file_path(filename)
            df.to_parquet(path, index=False)
            info = {
                "rows": len(df),
                "columns": len(df.columns),
                "path": str(path),
                "upload_time": datetime.now().isoformat(),
                "size_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            }
            with self._lock:
                self._file_info_store[filename] = info
                with open(self._info_path(), "w", encoding="utf-8") as f:
                    json.dump(self._file_info_store, f, indent=2)
        except Exception as e:  # pragma: no cover - best effort
            logger.error(f"Error saving uploaded data: {e}")

    # -- Public API ---------------------------------------------------------
    def add_file(self, filename: str, df: pd.DataFrame) -> None:
        """Persist ``df`` to disk and record its metadata."""
        # save synchronously to ensure metadata exists immediately
        self._save_to_disk(filename, df)
        try:

            try:
                asyncio.run(_cache_manager.clear())
            except Exception:
                pass

        except Exception as e:

            # Cache not available in standalone mode

            import logging

            logging.getLogger(__name__).info(f"Cache clear skipped: {e}")

    def load_dataframe(self, filename: str) -> pd.DataFrame:
        """Load a previously saved dataframe."""
        with self._lock:
            future = self._save_futures.get(filename)
        if future is not None:
            future.result()
            with self._lock:
                self._save_futures.pop(filename, None)
        return pd.read_parquet(self._get_file_path(filename))

    def load_mapping(self, filename: str) -> Dict[str, Any]:
        """Load saved column mapping for *filename* if present."""
        path = self._get_file_path(filename).with_suffix(".mapping.json")
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    return json.load(fh)
            except Exception as exc:  # pragma: no cover - best effort
                logger.error(
                    "Error loading mapping %s: %s",
                    safe_encode_text(filename),
                    exc,
                )
        return {}

    def save_mapping(self, filename: str, mapping: Dict[str, Any]) -> None:
        """Persist *mapping* for *filename*."""
        path = self._get_file_path(filename).with_suffix(".mapping.json")
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(mapping, fh, indent=2)
        except Exception as exc:  # pragma: no cover - best effort
            logger.error(
                "Error saving mapping %s: %s",
                safe_encode_text(filename),
                exc,
            )

    def get_all_data(self) -> Dict[str, pd.DataFrame]:
        return {fname: self.load_dataframe(fname) for fname in self.get_filenames()}

    def get_filenames(self) -> List[str]:
        with self._lock:
            names = set(self._file_info_store.keys()) | set(self._data_store.keys())
        return list(names)

    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        return self._file_info_store.copy()

    def save_column_mappings(self, filename: str, mappings: Dict[str, str]) -> None:
        """Persist column mappings for *filename* to disk."""
        with self._lock:
            info = self._file_info_store.setdefault(filename, {})
            info["column_mappings"] = mappings
            with open(self._info_path(), "w", encoding="utf-8") as f:
                json.dump(self._file_info_store, f, indent=2)

    def save_device_mappings(self, filename: str, mappings: Dict[str, Any]) -> None:
        """Persist device mappings for *filename* to disk."""
        with self._lock:
            info = self._file_info_store.setdefault(filename, {})
            info["device_mappings"] = mappings
            with open(self._info_path(), "w", encoding="utf-8") as f:
                json.dump(self._file_info_store, f, indent=2)

    def clear_all(self) -> None:
        with self._lock:
            self._data_store.clear()
            self._file_info_store.clear()
            try:
                for data_file in self.storage_dir.glob("*.parquet"):
                    data_file.unlink()
                if self._info_path().exists():
                    self._info_path().unlink()
            except Exception as e:  # pragma: no cover - best effort
                logger.error(f"Error clearing uploaded data: {e}")
        try:

            try:
                asyncio.run(_cache_manager.clear())
            except Exception:
                pass

        except Exception as e:

            # Cache not available in standalone mode

            import logging

            logging.getLogger(__name__).info(f"Cache clear skipped: {e}")

    def wait_for_pending_saves(self) -> None:
        """Block until all background save tasks have completed."""
        for fut in list(self._save_futures.values()):
            fut.result()
        self._save_futures.clear()


# Global persistent storage instance
uploaded_data_store = UploadedDataStore()

__all__ = [
    "UploadedDataStore",
    "uploaded_data_store",
]
