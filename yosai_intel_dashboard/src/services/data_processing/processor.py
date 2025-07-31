from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional, Tuple

import pandas as pd

from config.constants import DEFAULT_CHUNK_SIZE
from core.interfaces import ConfigProviderProtocol
from core.performance import get_performance_monitor
from monitoring.data_quality_monitor import (
    DataQualityMetrics,
    get_data_quality_monitor,
)
from services.streaming import StreamingService
from unicode_toolkit import safe_encode_text
from validation.security_validator import SecurityValidator

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from mapping.service import MappingService

logger = logging.getLogger(__name__)


class Processor:
    """Unified data loader with streaming and mapping helpers."""

    def __init__(
        self,
        base_data_path: str = "data",
        validator: Optional[SecurityValidator] = None,
        streaming_service: Optional[StreamingService] = None,
        mapping_service: MappingService | None = None,
        *,
        config: ConfigProviderProtocol | None = None,
    ) -> None:
        self.base_path = Path(base_data_path)
        self.mappings_file = self.base_path / "learned_mappings.json"
        self.session_storage = self.base_path.parent / "session_storage"
        self.validator = validator or SecurityValidator()
        self.streaming_service = streaming_service
        if mapping_service is None:
            from mapping.factories.service_factory import create_mapping_service

            mapping_service = create_mapping_service()
        self.mapping_service = mapping_service
        self.config = config

    # ------------------------------------------------------------------
    # Streaming helpers (from DataLoadingService)
    # ------------------------------------------------------------------
    def load_dataframe(self, source: Any) -> pd.DataFrame:
        """Load ``source`` into a validated and mapped dataframe."""
        analytics_cfg = getattr(self.config, "analytics", None) if self.config else None
        chunk_size = getattr(analytics_cfg, "chunk_size", DEFAULT_CHUNK_SIZE)
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
        return self.mapping_service.column_proc.process(df, "load").data

    def stream_file(
        self, source: Any, chunksize: int = DEFAULT_CHUNK_SIZE
    ) -> Iterator[pd.DataFrame]:
        """Yield cleaned chunks from ``source``."""
        monitor = get_performance_monitor()
        if isinstance(source, (str, Path)) or hasattr(source, "read"):
            for chunk in pd.read_csv(source, chunksize=chunksize, encoding="utf-8"):
                monitor.throttle_if_needed()
                chunk = self.validator.validate(chunk)
                yield self.mapping_service.column_proc.process(chunk, "stream").data
        else:
            df = self.validator.validate(source)
            yield self.mapping_service.column_proc.process(df, "stream").data

    def consume_stream(self, timeout: float = 1.0) -> Iterator[pd.DataFrame]:
        """Consume events from the configured streaming service."""
        if not self.streaming_service:
            logger.error("Streaming service not configured")
            return iter(())

        for raw in self.streaming_service.consume(timeout=timeout):
            try:
                data = json.loads(raw)
            except Exception as exc:  # pragma: no cover - best effort
                logger.error("Invalid event data: %s", exc)
                continue
            df = pd.DataFrame([data])
            df = self.validator.validate(df)
            yield self.mapping_service.column_proc.process(df, "stream").data

    # ------------------------------------------------------------------
    # Uploaded data processing (from DataLoader)
    # ------------------------------------------------------------------
    def get_processed_database(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Return uploaded data combined with mapping metadata."""
        mappings = self._load_consolidated_mappings()
        uploaded = self._get_uploaded_data()
        if not uploaded:
            return pd.DataFrame(), {}
        df, meta = self._apply_mappings_and_combine(uploaded, mappings)
        if not df.empty:
            metrics = self._evaluate_data_quality(df)
            get_data_quality_monitor().emit(metrics)
        return df, meta

    # Internal helpers -------------------------------------------------
    def _load_consolidated_mappings(self) -> Dict[str, Any]:
        try:
            data = {}
            if self.mappings_file.exists():
                with open(
                    self.mappings_file,
                    "r",
                    encoding="utf-8",
                    errors="replace",
                ) as fh:
                    data = json.load(fh)

            from services.upload_data_service import (
                get_uploaded_filenames,
                load_mapping,
            )

            for fname in get_uploaded_filenames():
                try:
                    m = load_mapping(fname)
                    if m:
                        data[fname] = {
                            "filename": fname,
                            "column_mappings": m,
                            "device_mappings": {},
                        }
                except Exception as exc:  # pragma: no cover - best effort
                    logger.error(
                        "Error loading mapping for %s: %s",
                        safe_encode_text(fname),
                        exc,
                    )

            return data
        except Exception as exc:  # pragma: no cover - best effort
            logger.error(f"Error loading mappings: {exc}")
            return {}

    def _get_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        try:
            from services.upload_data_service import get_uploaded_data

            data = get_uploaded_data()
            if not data:
                logger.info("No uploaded data found")
                return {}

            logger.info("Found %d uploaded files", len(data))
            for name, df in data.items():
                logger.info(
                    "%s: %d rows",
                    safe_encode_text(name),
                    len(df),
                )
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
            "column_mappings": {},
        }

        for filename, df in uploaded.items():
            try:
                processed = self.mapping_service.process_upload(df, filename)
                enriched = processed.devices.data
                enriched["source_file"] = filename
                enriched["processed_at"] = datetime.now()

                if filename in mappings:
                    meta["column_mappings"][filename] = mappings[filename].get(
                        "column_mappings", {}
                    )

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

    # ------------------------------------------------------------------
    def _evaluate_data_quality(self, df: pd.DataFrame) -> DataQualityMetrics:
        """Calculate basic data quality metrics for ``df``."""
        if df.empty:
            return DataQualityMetrics(0.0, 0.0, 4)

        total_cells = df.size
        missing_ratio = (
            float(df.isnull().sum().sum()) / total_cells if total_cells else 0.0
        )

        numeric = df.select_dtypes(include="number")
        if not numeric.empty and (numeric.std(ddof=0) != 0).any():
            zscores = (numeric - numeric.mean()).abs() / numeric.std(ddof=0)
            outliers = (zscores > 3).sum().sum()
            outlier_ratio = float(outliers) / numeric.size if numeric.size else 0.0
        else:
            outlier_ratio = 0.0

        required = {"timestamp", "person_id", "door_id", "access_result"}
        schema_violations = len(required - set(df.columns))

        return DataQualityMetrics(missing_ratio, outlier_ratio, schema_violations)


__all__ = ["Processor"]
