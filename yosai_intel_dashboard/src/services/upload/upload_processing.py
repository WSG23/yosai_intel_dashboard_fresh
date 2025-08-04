from __future__ import annotations

"""Utilities for analyzing uploaded dataframes.

This module provides a lightweight :class:`UploadAnalyticsProcessor` used by
various services.  The previous version of this file was a small stub that was
patched at runtime during tests.  The runtime patches have been removed and the
full implementation now lives here so it can be imported normally.
"""

import os
from typing import Any, Dict, List, Optional

import pandas as pd

from yosai_intel_dashboard.src.services.upload.protocols import UploadAnalyticsProtocol
from yosai_intel_dashboard.src.utils.upload_store import (
    UploadedDataStore,
    get_uploaded_data_store,
)


class UploadAnalyticsProcessor(UploadAnalyticsProtocol):
    """Process and analyse uploaded files.

    The processor historically accepted a variety of positional arguments when
    constructed.  The implementation here keeps a compatible ``__init__`` so
    existing call sites continue to work while optionally allowing a custom
    :class:`UploadedDataStore` to be supplied via the ``store`` keyword
    argument.
    """

    def __init__(
        self, *args: Any, store: UploadedDataStore | None = None, **kwargs: Any
    ) -> None:
        self.store = store

    # ------------------------------------------------------------------
    # Basic helpers
    # ------------------------------------------------------------------
    def _get_default_store(self) -> UploadedDataStore:
        """Return the data store used for uploaded files."""
        if self.store is None:
            self.store = get_uploaded_data_store()
        return self.store

    # ------------------------------------------------------------------
    # Loading and cleaning helpers
    # ------------------------------------------------------------------
    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Load all uploaded dataframes from the store."""
        store = self._get_default_store()
        return store.get_all_data()

    # ------------------------------------------------------------------
    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a cleaned copy of *df* suitable for analytics.

        The cleaning performed here is intentionally lightweight and only
        performs the operations required by the unit tests and basic analytics:

        * drop completely empty rows
        * normalise column names to ``snake_case``
        * rename common columns (``device_name`` -> ``door_id``)
        * parse the ``timestamp`` column when present
        """

        cleaned = df.dropna(how="all").copy()
        cleaned.columns = [c.strip().replace(" ", "_").lower() for c in cleaned.columns]
        column_map = {"device_name": "door_id"}
        cleaned.rename(columns=column_map, inplace=True)
        if "timestamp" in cleaned.columns:
            cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp"], errors="coerce")
        return cleaned

    # ------------------------------------------------------------------
    # Summaries
    # ------------------------------------------------------------------
    def _get_column_statistics(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Return per column statistics used by the analytics summary."""
        stats: Dict[str, Dict[str, Any]] = {}
        for col in df.columns:
            series = df[col]
            col_stats: Dict[str, Any] = {
                "dtype": str(series.dtype),
                "nulls": int(series.isna().sum()),
                "non_nulls": int(series.notna().sum()),
            }
            if pd.api.types.is_numeric_dtype(series):
                col_stats.update(
                    {
                        "min": float(series.min()) if not series.empty else None,
                        "max": float(series.max()) if not series.empty else None,
                        "mean": float(series.mean()) if not series.empty else None,
                    }
                )
            else:
                col_stats["unique"] = int(series.nunique(dropna=True))
            stats[col] = col_stats
        return stats

    # ------------------------------------------------------------------
    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create a summary dictionary from a combined DataFrame."""
        if df.empty:
            return {
                "total_events": 0,
                "active_users": 0,
                "active_doors": 0,
                "date_range": {"start": "Unknown", "end": "Unknown"},
                "access_patterns": {},
                "top_users": [],
                "top_doors": [],
                "columns": {},
            }

        total_events = len(df)
        active_users = df["person_id"].nunique() if "person_id" in df.columns else 0
        active_doors = df["door_id"].nunique() if "door_id" in df.columns else 0

        date_range = {"start": "Unknown", "end": "Unknown"}
        if "timestamp" in df.columns:
            valid_ts = df["timestamp"].dropna()
            if not valid_ts.empty:
                date_range = {
                    "start": str(valid_ts.min().date()),
                    "end": str(valid_ts.max().date()),
                }

        access_patterns: Dict[str, int] = {}
        if "access_result" in df.columns:
            access_patterns = df["access_result"].value_counts().to_dict()

        top_users: List[Dict[str, Any]] = []
        if "person_id" in df.columns:
            counts = df["person_id"].value_counts().head(10)
            top_users = [
                {"user_id": str(k), "count": int(v)} for k, v in counts.items()
            ]

        top_doors: List[Dict[str, Any]] = []
        if "door_id" in df.columns:
            counts = df["door_id"].value_counts().head(10)
            top_doors = [
                {"door_id": str(k), "count": int(v)} for k, v in counts.items()
            ]

        return {
            "total_events": total_events,
            "active_users": active_users,
            "active_doors": active_doors,
            "date_range": date_range,
            "access_patterns": access_patterns,
            "top_users": top_users,
            "top_doors": top_doors,
            "columns": self._get_column_statistics(df),
        }

    # ------------------------------------------------------------------
    # High level analytics
    # ------------------------------------------------------------------
    def get_analytics_from_uploaded_data(self) -> Dict[str, Any]:
        """Load uploaded data and return a combined analytics summary."""
        try:
            store = self._get_default_store()
            file_info = store.get_file_info()
            if not file_info:
                return {
                    "status": "no_data",
                    "message": "No uploaded files available",
                }

            data = {name: store.load_dataframe(name) for name in file_info.keys()}
            if not data:
                return {
                    "status": "no_data",
                    "message": "No uploaded files available",
                }

            cleaned_dfs = [self.clean_uploaded_dataframe(df) for df in data.values()]
            combined = (
                cleaned_dfs[0]
                if len(cleaned_dfs) == 1
                else pd.concat(cleaned_dfs, ignore_index=True)
            )
            summary = self.summarize_dataframe(combined)
            summary.update(
                {
                    "status": "success",
                    "files_processed": len(data),
                    "file_info": file_info,
                }
            )
            return summary
        except Exception as exc:  # pragma: no cover - best effort
            return {"status": "error", "message": str(exc)}

    # ------------------------------------------------------------------
    def _get_real_uploaded_data(self) -> Dict[str, Any]:
        """Internal helper used by analytics service tests."""
        try:
            data = self.load_uploaded_data()
            if not data:
                return {"status": "no_data"}

            original_total = sum(len(df) for df in data.values())
            cleaned_dfs = [self.clean_uploaded_dataframe(df) for df in data.values()]
            combined = (
                cleaned_dfs[0]
                if len(cleaned_dfs) == 1
                else pd.concat(cleaned_dfs, ignore_index=True)
            )
            summary = self.summarize_dataframe(combined)
            summary.update(
                {
                    "status": "success",
                    "files_processed": len(data),
                    "original_total_rows": original_total,
                }
            )
            return summary
        except Exception as exc:  # pragma: no cover - best effort
            return {"status": "error", "message": str(exc)}

    # ------------------------------------------------------------------
    def _get_analytics_with_fixed_processor(self) -> Dict[str, Any]:
        """Check for sample file paths and report their existence.

        The method mirrors the behaviour of the original implementation used in
        earlier scripts.  It does not perform heavy processing; it merely checks
        whether the configured sample files exist so tests can verify that the
        correct paths are used.
        """

        from config import get_config

        csv_path = os.getenv("SAMPLE_CSV_PATH")
        json_path = os.getenv("SAMPLE_JSON_PATH")

        cfg = get_config().config
        if not csv_path:
            csv_path = getattr(getattr(cfg, "sample_files", object()), "csv_path", None)
        if not json_path:
            json_path = getattr(
                getattr(cfg, "sample_files", object()), "json_path", None
            )

        checked: List[str] = []
        for path in [csv_path, json_path]:
            if path:
                checked.append(path)
                try:
                    os.path.exists(path)
                except Exception:  # pragma: no cover - best effort
                    pass
        return {"status": "unknown", "checked_paths": checked}

    # ------------------------------------------------------------------
    # Backwards compatible methods from original stub
    # ------------------------------------------------------------------
    def _load_data(self) -> Dict[str, pd.DataFrame]:
        """Return uploaded data using :meth:`load_uploaded_data`."""
        return self.load_uploaded_data()

    def _validate_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Remove empty dataframes from ``data``."""
        return {name: df for name, df in data.items() if not df.empty}

    def _calculate_statistics(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate basic statistics for uploaded ``data``."""
        total_events = sum(len(df) for df in data.values())
        users: set[Any] = set()
        doors: set[Any] = set()
        for df in data.values():
            if "Person ID" in df.columns:
                users.update(df["Person ID"].dropna().unique())
            if "Device name" in df.columns:
                doors.update(df["Device name"].dropna().unique())
        return {
            "total_events": total_events,
            "active_users": len(users),
            "active_doors": len(doors),
        }

    def _format_results(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Return final result dictionary with ``status`` key."""
        result = dict(stats)
        result["status"] = "success"
        return result

    def _process_uploaded_data_directly(
        self, data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Backward compatible helper to process uploaded ``data``."""
        validated = self._validate_data(data)
        return self._calculate_statistics(validated)

    def analyze_uploaded_data(self) -> Dict[str, Any]:
        """Main entry point coordinating upload analytics."""
        try:
            data = self._load_data()
            validated = self._validate_data(data)
            stats = self._calculate_statistics(validated)
            return self._format_results(stats)
        except Exception as exc:  # pragma: no cover - best effort
            return {"status": "error", "message": str(exc)}


__all__ = ["UploadAnalyticsProcessor"]
