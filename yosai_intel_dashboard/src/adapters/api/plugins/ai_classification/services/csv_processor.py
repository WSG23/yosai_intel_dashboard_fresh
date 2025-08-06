"""Enhanced CSV processing service with optional Polars optimization"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from yosai_intel_dashboard.src.services.data_processing.file_processor import (
    FileProcessor,
)

# Optional Polars import with pandas fallback
try:
    import polars as pl  # type: ignore

    POLARS_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    POLARS_AVAILABLE = False
    pl = None  # type: ignore

logger = logging.getLogger(__name__)

from .base import BaseCSVProcessor


class CSVProcessorService(BaseCSVProcessor):
    """Process CSV data with optional Polars acceleration"""

    def __init__(self, repository, japanese_handler, config) -> None:
        super().__init__(repository, japanese_handler, config)

        # Determine backend based on config and availability
        self.use_polars = POLARS_AVAILABLE and getattr(config, "use_polars", True)

        if self.use_polars:
            self.logger.info("Using Polars for CSV processing")
        else:
            self.logger.info("Using Pandas for CSV processing")

    def process_csv_data(
        self,
        csv_data: bytes,
        filename: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """Process raw CSV bytes and return analysis information"""

        try:
            if self.use_polars and len(csv_data) > 1024 * 1024:
                return self._process_with_polars(csv_data, filename, session_id)
            return self._process_with_pandas(csv_data, filename, session_id)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("CSV processing failed for %s: %s", filename, exc)
            return {
                "success": False,
                "error": f"Failed to process CSV: {exc}",
                "session_id": session_id,
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _process_with_polars(
        self,
        csv_data: bytes,
        filename: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """Read and analyse CSV using Polars"""

        assert pl is not None  # for type checking

        try:
            df_polars = pl.read_csv(
                csv_data,
                infer_schema_length=1000,
                try_parse_dates=True,
                ignore_errors=True,
            )
            df_pandas = df_polars.to_pandas()
        except Exception as exc:  # pragma: no cover - fallback
            self.logger.warning("Polars failed, falling back to pandas: %s", exc)
            return self._process_with_pandas(csv_data, filename, session_id)

        result = self._analyze_dataframe(df_pandas, filename, session_id)
        result["processor"] = "polars"
        return result

    def _process_with_pandas(
        self,
        csv_data: bytes,
        filename: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """Read and analyse CSV using Pandas"""

        encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
        csv_text: Optional[str] = None

        for enc in encodings:
            try:
                csv_text = csv_data.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if csv_text is None:
            csv_text = csv_data.decode("utf-8", errors="replace")

        df = FileProcessor.read_large_csv(
            pd.io.common.StringIO(csv_text),
            dtype=str,
            keep_default_na=False,
            na_filter=False,
        )

        result = self._analyze_dataframe(df, filename, session_id)
        result["processor"] = "pandas"
        return result

    def _analyze_dataframe(
        self,
        df: pd.DataFrame,
        filename: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """Gather statistics and optional Japanese text detection"""

        df.columns = df.columns.str.strip()

        stats = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "memory_usage": int(df.memory_usage(deep=True).sum()),
            "null_percentage": (df.isnull().sum() / len(df) * 100).to_dict(),
        }

        dtypes_info: Dict[str, Any] = {}
        for col in df.columns:
            sample_values = df[col].dropna().head(10).tolist()
            dtypes_info[col] = {
                "sample_values": sample_values,
                "unique_count": int(df[col].nunique()),
                "null_count": int(df[col].isnull().sum()),
            }

        japanese_columns: List[str] = []
        japanese_seen: set[str] = set()
        if self.japanese_handler:
            for col in df.columns:
                if self.japanese_handler.contains_japanese(col):
                    if col not in japanese_seen:
                        japanese_columns.append(col)
                        japanese_seen.add(col)
                    continue

                sample_text = " ".join(str(v) for v in df[col].dropna().head(5))
                if (
                    self.japanese_handler.contains_japanese(sample_text)
                    and col not in japanese_seen
                ):
                    japanese_columns.append(col)
                    japanese_seen.add(col)

        if self.repository:
            try:
                self.repository.store_processing_result(
                    session_id,
                    {
                        "filename": filename,
                        "stats": stats,
                        "dtypes_info": dtypes_info,
                        "japanese_columns": japanese_columns,
                        "processed_at": pd.Timestamp.now().isoformat(),
                    },
                )
            except Exception as exc:  # pragma: no cover - repository errors
                self.logger.warning("Failed to store processing result: %s", exc)

        return {
            "success": True,
            "session_id": session_id,
            "filename": filename,
            "stats": stats,
            "dtypes_info": dtypes_info,
            "japanese_columns": japanese_columns,
            "dataframe": df,
        }

    # ------------------------------------------------------------------
    # Public helper
    # ------------------------------------------------------------------
    def get_processing_capabilities(self) -> Dict[str, Any]:
        """Return backend capabilities and feature info"""

        return {
            "polars_available": POLARS_AVAILABLE,
            "using_polars": self.use_polars,
            "max_file_size": (
                "100MB with Pandas, 1GB+ with Polars"
                if POLARS_AVAILABLE
                else "100MB with Pandas"
            ),
            "supported_encodings": [
                "utf-8",
                "utf-8-sig",
                "latin1",
                "cp1252",
            ],
            "features": [
                "Unicode handling",
                "Japanese text detection",
                "Data type inference",
                "Memory optimization",
                "Error recovery",
            ],
        }


class PandasOnlyCSVProcessor(BaseCSVProcessor):
    """Fallback CSV processor using only Pandas"""

    def __init__(self, repository, japanese_handler, config) -> None:
        super().__init__(repository, japanese_handler, config)
        self.logger.info("Using Pandas-only CSV processor")

    def process_csv_data(
        self, csv_data: bytes, filename: str, session_id: str
    ) -> Dict[str, Any]:
        service = CSVProcessorService(
            self.repository, self.japanese_handler, self.config
        )
        service.use_polars = False
        return service.process_csv_data(csv_data, filename, session_id)


def create_csv_processor(repository, japanese_handler, config) -> CSVProcessorService:
    """Factory returning the best available CSV processor"""

    if POLARS_AVAILABLE:
        return CSVProcessorService(repository, japanese_handler, config)
    logger.info("Polars not available, using Pandas-only processor")
    return PandasOnlyCSVProcessor(repository, japanese_handler, config)


__all__ = [
    "CSVProcessorService",
    "PandasOnlyCSVProcessor",
    "create_csv_processor",
    "POLARS_AVAILABLE",
]
