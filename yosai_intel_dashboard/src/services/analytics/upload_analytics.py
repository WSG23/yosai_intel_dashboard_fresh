"""Analytics helpers for uploaded DataFrame objects."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
from pydantic import BaseModel, ConfigDict, ValidationError

from yosai_intel_dashboard.src.services.analytics_summary import (
    summarize_dataframe as _summarize_dataframe,
)
from yosai_intel_dashboard.src.services.chunked_analysis import analyze_with_chunking
from yosai_intel_dashboard.src.services.upload.protocols import UploadAnalyticsProtocol
from yosai_intel_dashboard.src.utils.upload_store import get_uploaded_data_store
from validation.data_validator import DataValidator, DataValidatorProtocol
from .unicode import normalize_text


class _EventsFrameModel(BaseModel):
    """Schema for required dataframe columns used in analytics."""

    timestamp: pd.Series
    events: pd.Series

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")


def _validate_events_frame(df: pd.DataFrame) -> None:
    """Ensure ``df`` contains required columns prior to normalization."""

    try:
        _EventsFrameModel(**df.to_dict(orient="series"))
    except ValidationError as exc:  # pragma: no cover - explicit error
        missing = {err["loc"][0] for err in exc.errors()}
        cols = ", ".join(sorted(missing))
        raise ValueError(f"missing required columns: {cols}") from exc


def summarize_dataframes(dfs: List[pd.DataFrame]) -> Dict[str, Any]:
    """Combine ``dfs`` and return a summary dictionary."""
    if not dfs:
        return {"status": "no_data"}
    for df in dfs:
        _validate_events_frame(df)
    combined = pd.concat(dfs, ignore_index=True)
    summary = _summarize_dataframe(combined)
    summary.update({"status": "success", "files_processed": len(dfs)})
    return summary


def run_anomaly_detection(
    df: pd.DataFrame, validator: DataValidatorProtocol | None = None
) -> Dict[str, Any]:
    """Run anomaly detection using chunked analysis."""
    validator = validator or DataValidator(required_columns=["timestamp", "person_id"])
    return analyze_with_chunking(df, validator, ["anomaly"])


class UploadAnalyticsProcessor(UploadAnalyticsProtocol):
    """Process and analyze uploaded access control data."""

    def __init__(
        self,
        validator: "UploadSecurityProtocol",
        processor: "ProcessorProtocol",
        callback_manager: "TrulyUnifiedCallbacks",
        analytics_config: "AnalyticsConstants",
        event_bus: "EventBusProtocol",
    ) -> None:
        self.validator = validator
        self.processor = processor
        self.callback_manager = callback_manager
        self.analytics_config = analytics_config
        self.event_bus = event_bus

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def analyze_uploaded_data(self) -> Dict[str, Any]:
        """Public entry point for analysis of uploaded data."""
        return self.get_analytics_from_uploaded_data()

    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Retrieve all uploaded data from the shared store."""
        store = get_uploaded_data_store()
        return store.get_all_data()

    def get_analytics_from_uploaded_data(self) -> Dict[str, Any]:
        """Load uploaded data and return aggregated analytics."""
        try:
            data = self._load_data()
            if not data:
                return {"status": "no_data"}
            stats = self._process_uploaded_data_directly(data)
            return self._format_results(stats)
        except Exception as exc:  # pragma: no cover - best effort
            return {"status": "error", "message": str(exc)}

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop empty rows/columns and normalize column names in ``df``."""
        if df.empty:
            return df.copy()

        cleaned = df.dropna(how="all", axis=0).dropna(how="all", axis=1).copy()
        cleaned.columns = [
            normalize_text(c).strip().lower().replace(" ", "_")
            for c in cleaned.columns
        ]
        cleaned = cleaned.rename(
            columns={"device_name": "door_id", "event_time": "timestamp"}
        )
        if "timestamp" in cleaned.columns:
            cleaned["timestamp"] = pd.to_datetime(
                cleaned["timestamp"], errors="coerce"
            )
        cleaned = cleaned.dropna(how="all", axis=0)
        cleaned.columns = [normalize_text(c) for c in cleaned.columns]
        return cleaned

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return basic statistics for ``df``."""
        return {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "memory_usage": int(df.memory_usage(deep=True).sum()),
            "null_counts": {col: int(df[col].isna().sum()) for col in df.columns},
        }

    # ------------------------------------------------------------------
    # Internal helpers routed through public methods
    # ------------------------------------------------------------------
    def _load_data(self) -> Dict[str, pd.DataFrame]:
        """Return uploaded data using :meth:`load_uploaded_data`."""
        return self.load_uploaded_data()

    def _validate_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Clean uploaded dataframes and drop empty ones."""
        cleaned: Dict[str, pd.DataFrame] = {}
        for name, df in data.items():
            cleaned_df = self.clean_uploaded_dataframe(df)
            if not cleaned_df.empty:
                cleaned[name] = cleaned_df
        return cleaned

    def _calculate_statistics(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate statistics for validated ``data``."""
        if not data:
            return {
                "rows": 0,
                "columns": 0,
                "column_names": [],
                "dtypes": {},
                "memory_usage": 0,
                "null_counts": {},
                "total_events": 0,
                "active_users": 0,
                "active_doors": 0,
                "date_range": {"start": "Unknown", "end": "Unknown"},
            }

        combined = pd.concat(list(data.values()), ignore_index=True)
        summary = self.summarize_dataframe(combined)

        active_users = (
            combined["person_id"].nunique() if "person_id" in combined.columns else 0
        )
        active_doors = (
            combined["door_id"].nunique() if "door_id" in combined.columns else 0
        )

        date_range = {"start": "Unknown", "end": "Unknown"}
        if "timestamp" in combined.columns:
            ts = pd.to_datetime(combined["timestamp"], errors="coerce").dropna()
            if not ts.empty:
                date_range = {
                    "start": str(ts.min().date()),
                    "end": str(ts.max().date()),
                }

        summary.update(
            {
                "column_names": list(combined.columns),
                "total_events": int(combined.shape[0]),
                "active_users": int(active_users),
                "active_doors": int(active_doors),
                "date_range": date_range,
            }
        )
        return summary

    def _format_results(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Return final result dictionary with ``status`` key."""
        result = dict(stats)
        result["status"] = result.get("status", "success")
        return result

    # ------------------------------------------------------------------
    def _process_uploaded_data_directly(
        self, data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Backward compatible helper to process uploaded ``data``."""

        validated = self._validate_data(data)
        return self._calculate_statistics(validated)


# Expose commonly used methods at module level for convenience
get_analytics_from_uploaded_data = (
    UploadAnalyticsProcessor.get_analytics_from_uploaded_data
)
clean_uploaded_dataframe = UploadAnalyticsProcessor.clean_uploaded_dataframe
summarize_dataframe = UploadAnalyticsProcessor.summarize_dataframe


__all__ = [
    "summarize_dataframes",
    "run_anomaly_detection",
    "UploadAnalyticsProcessor",
    "get_analytics_from_uploaded_data",
    "clean_uploaded_dataframe",
    "summarize_dataframe",
]
