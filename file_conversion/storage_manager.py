"""Manage Parquet file storage with metadata tracking."""

from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from core.callback_events import CallbackEvent
from core.callbacks import UnifiedCallbackManager
from core.container import get_unicode_processor
from core.protocols import UnicodeProcessorProtocol

_logger = logging.getLogger(__name__)


class StorageManager:
    """Handle saving/loading Parquet files and tracking metadata."""

    def __init__(
        self,
        base_dir: Path | str = "converted_data",
        *,
        unicode_processor: UnicodeProcessorProtocol | None = None,
    ) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_path = self.base_dir / "metadata.json"
        self._metadata: Dict[str, Any] = {}
        self.unified_callbacks = UnifiedCallbackManager()
        self.unicode_processor = unicode_processor or get_unicode_processor()
        self._load_metadata()

    # -- metadata helpers -------------------------------------------------
    def _load_metadata(self) -> None:
        try:
            if self._metadata_path.exists():
                with open(self._metadata_path, "r", encoding="utf-8") as fh:
                    self._metadata = json.load(fh)
        except Exception as exc:  # pragma: no cover - best effort
            _logger.error("Failed to load metadata: %s", exc)
            self._metadata = {}

    def _save_metadata(self) -> None:
        try:
            with open(self._metadata_path, "w", encoding="utf-8") as fh:
                json.dump(self._metadata, fh, indent=2, default=str)
        except Exception as exc:  # pragma: no cover - best effort
            _logger.error("Failed to save metadata: %s", exc)

    # -- public API -------------------------------------------------------
    def migrate_pkl_to_parquet(self, pkl_path: Path) -> Tuple[bool, str]:
        """Convert ``pkl_path`` to Parquet in base directory."""
        parquet_path = self.base_dir / pkl_path.with_suffix(".parquet").name
        self.unified_callbacks.trigger(
            CallbackEvent.FILE_PROCESSING_START,
            str(pkl_path),
        )
        try:
            if not pkl_path.exists():
                raise FileNotFoundError(f"Pickle file not found: {pkl_path}")

            df = pd.read_pickle(pkl_path)
            df_clean = self.unicode_processor.sanitize_dataframe(df)
            df_clean.to_parquet(parquet_path, index=False, compression="snappy")

            self._metadata[parquet_path.name] = {
                "original_file": str(pkl_path),
                "rows": len(df_clean),
                "columns": len(df_clean.columns),
                "converted_at": datetime.utcnow().isoformat(),
            }
            self._save_metadata()

            self.unified_callbacks.trigger(
                CallbackEvent.FILE_PROCESSING_COMPLETE,
                str(pkl_path),
                {"parquet_file": str(parquet_path)},
            )
            return True, f"Converted {pkl_path} to {parquet_path}"
        except Exception as exc:  # pragma: no cover - best effort
            _logger.error("Failed to migrate pkl: %s", exc)
            self.unified_callbacks.trigger(
                CallbackEvent.FILE_PROCESSING_ERROR,
                str(pkl_path),
                {"error": str(exc)},
            )
            return False, str(exc)

    def save_dataframe(self, df: pd.DataFrame, name: str) -> Tuple[bool, str]:
        """Save ``df`` to a Parquet file under ``name`` with metadata."""
        try:
            df_clean = self.unicode_processor.sanitize_dataframe(df)
            parquet_path = self.base_dir / f"{name}.parquet"
            df_clean.to_parquet(parquet_path, index=False, compression="snappy")
            self._metadata[parquet_path.name] = {
                "rows": len(df_clean),
                "columns": len(df_clean.columns),
                "saved_at": datetime.utcnow().isoformat(),
            }
            self._save_metadata()
            return True, f"Saved {parquet_path}"
        except Exception as exc:  # pragma: no cover - best effort
            _logger.error("Failed to save DataFrame: %s", exc)
            return False, str(exc)

    def load_dataframe(self, name: str) -> Tuple[Optional[pd.DataFrame], str]:
        """Load a Parquet file previously saved."""
        parquet_path = self.base_dir / f"{name}.parquet"
        try:
            if not parquet_path.exists():
                return None, f"File not found: {parquet_path}"
            df = pd.read_parquet(parquet_path)
            return df, ""
        except Exception as exc:  # pragma: no cover - best effort
            _logger.error("Failed to load DataFrame: %s", exc)
            return None, str(exc)


__all__ = ["StorageManager"]
