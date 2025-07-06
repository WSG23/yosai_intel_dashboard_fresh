import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple

import pandas as pd
from config.dynamic_config import dynamic_config
from core.performance import get_performance_monitor

from services.data_validation import DataValidationService
from utils.mapping_helpers import map_and_clean

logger = logging.getLogger(__name__)


class Processor:
    """Unified data loader with streaming and mapping helpers."""

    def __init__(
        self,
        base_data_path: str = "data",
        validator: Optional[DataValidationService] = None,
    ) -> None:
        self.base_path = Path(base_data_path)
        self.mappings_file = self.base_path / "learned_mappings.json"
        self.session_storage = self.base_path.parent / "session_storage"
        self.validator = validator or DataValidationService()

    # ------------------------------------------------------------------
    # Streaming helpers (from DataLoadingService)
    # ------------------------------------------------------------------
    def load_dataframe(self, source: Any) -> pd.DataFrame:
        """Load ``source`` into a validated and mapped dataframe."""
        chunk_size = getattr(dynamic_config.analytics, "chunk_size", 50000)
        monitor = get_performance_monitor()

        if isinstance(source, (str, Path)) or hasattr(source, "read"):
            reader = pd.read_csv(source, encoding="utf-8", chunksize=chunk_size)
            chunks = []
            for chunk in reader:
                monitor.throttle_if_needed()
                chunks.append(chunk)
            df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
        else:
            df = source
        df = self.validator.validate(df)
        return map_and_clean(df)

    def stream_file(self, source: Any, chunksize: int = 50000) -> Iterator[pd.DataFrame]:
        """Yield cleaned chunks from ``source``."""
        monitor = get_performance_monitor()
        if isinstance(source, (str, Path)) or hasattr(source, "read"):
            for chunk in pd.read_csv(source, chunksize=chunksize, encoding="utf-8"):
                monitor.throttle_if_needed()
                chunk = self.validator.validate(chunk)
                yield map_and_clean(chunk)
        else:
            df = self.validator.validate(source)
            yield map_and_clean(df)

    # ------------------------------------------------------------------
    # Uploaded data processing (from DataLoader)
    # ------------------------------------------------------------------
    def get_processed_database(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Return uploaded data combined with mapping metadata."""
        mappings = self._load_consolidated_mappings()
        uploaded = self._get_uploaded_data()
        if not uploaded:
            return pd.DataFrame(), {}
        return self._apply_mappings_and_combine(uploaded, mappings)

    # Internal helpers -------------------------------------------------
    def _load_consolidated_mappings(self) -> Dict[str, Any]:
        try:
            if self.mappings_file.exists():
                with open(
                    self.mappings_file,
                    "r",
                    encoding="utf-8",
                    errors="replace",
                ) as fh:
                    return json.load(fh)
            return {}
        except Exception as exc:  # pragma: no cover - best effort
            logger.error(f"Error loading mappings: {exc}")
            return {}

    def _get_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        try:
            from pages.file_upload import get_uploaded_data

            data = get_uploaded_data()
            if not data:
                logger.info("No uploaded data found")
                return {}

            logger.info("Found %d uploaded files", len(data))
            for name, df in data.items():
                logger.info("%s: %d rows", name, len(df))
            return data
        except ImportError:
            logger.error("Could not import uploaded data from file_upload")
            return {}
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Error getting uploaded data: %s", exc)
            return {}

    def _apply_mappings_and_combine(
        self, uploaded: Dict[str, pd.DataFrame], mappings: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        combined: list[pd.DataFrame] = []
        meta = {
            "total_files": len(uploaded),
            "processed_files": 0,
            "total_records": 0,
            "unique_users": set(),
            "unique_devices": set(),
            "date_range": {"start": None, "end": None},
        }

        for filename, df in uploaded.items():
            try:
                mapped = self._apply_column_mappings(df, filename, mappings)
                enriched = self._apply_device_mappings(mapped, filename, mappings)
                enriched["source_file"] = filename
                enriched["processed_at"] = datetime.now()

                combined.append(enriched)
                meta["processed_files"] += 1
                meta["total_records"] += len(enriched)

                if "person_id" in enriched.columns:
                    meta["unique_users"].update(enriched["person_id"].dropna().unique())
                if "door_id" in enriched.columns:
                    meta["unique_devices"].update(enriched["door_id"].dropna().unique())

                if "timestamp" in enriched.columns:
                    dates = pd.to_datetime(
                        enriched["timestamp"], errors="coerce"
                    ).dropna()
                    if not dates.empty:
                        if meta["date_range"]["start"] is None:
                            meta["date_range"]["start"] = dates.min()
                            meta["date_range"]["end"] = dates.max()
                        else:
                            meta["date_range"]["start"] = min(
                                meta["date_range"]["start"], dates.min()
                            )
                            meta["date_range"]["end"] = max(
                                meta["date_range"]["end"], dates.max()
                            )
            except Exception as exc:  # pragma: no cover - best effort
                logger.error("Error processing %s: %s", filename, exc)

        if combined:
            final_df = pd.concat(combined, ignore_index=True)
            meta["unique_users"] = len(meta["unique_users"])
            meta["unique_devices"] = len(meta["unique_devices"])
            return final_df, meta

        return pd.DataFrame(), meta

    def _apply_column_mappings(
        self, df: pd.DataFrame, filename: str, mappings: Dict[str, Any]
    ) -> pd.DataFrame:
        for mapping in mappings.values():
            if mapping.get("filename") == filename:
                cols = mapping.get("column_mappings", {})
                if cols:
                    return df.rename(columns=cols)

        standard = {
            "Timestamp": "timestamp",
            "Person ID": "person_id",
            "Token ID": "token_id",
            "Device name": "door_id",
            "Access result": "access_result",
        }
        return df.rename(columns=standard)

    def _apply_device_mappings(
        self, df: pd.DataFrame, filename: str, mappings: Dict[str, Any]
    ) -> pd.DataFrame:
        if "door_id" not in df.columns:
            return df

        device_mappings = {}
        for mapping in mappings.values():
            if mapping.get("filename") == filename:
                device_mappings = mapping.get("device_mappings", {})
                break
        if not device_mappings:
            return df

        attrs_df = pd.DataFrame.from_dict(device_mappings, orient="index")
        attrs_df.index.name = "door_id"
        attrs_df.reset_index(inplace=True)
        return df.merge(attrs_df, on="door_id", how="left")


__all__ = ["Processor"]
