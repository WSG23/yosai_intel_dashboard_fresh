from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

try:  # pragma: no cover - optional dependency for protocol typing
    from yosai_intel_dashboard.src.services.upload.protocols import (
        UploadAnalyticsProtocol,
    )
except Exception:  # pragma: no cover - fallback for minimal environments
    from typing import Protocol

    class UploadAnalyticsProtocol(Protocol):
        def analyze_uploaded_data(self) -> Dict[str, Any]: ...  # noqa: D401

        def load_uploaded_data(self) -> Dict[str, pd.DataFrame]: ...


class UploadAnalyticsProcessor(UploadAnalyticsProtocol):
    """Process uploaded data and compute simple analytics."""

    def __init__(
        self,
        validator: Optional[Any] = None,
        processor: Optional[Any] = None,
        data_store: Optional[Any] = None,
    ) -> None:
        self.validator = validator
        self.processor = processor
        self.data_store = (
            data_store if data_store is not None else self._get_default_store()
        )

    # ------------------------------------------------------------------
    def _get_default_store(self) -> Dict[str, pd.DataFrame]:
        """Return default in-memory data store."""
        return {}

    # ------------------------------------------------------------------
    def _load_data(self) -> Dict[str, pd.DataFrame]:
        """Return uploaded data using :meth:`load_uploaded_data`."""
        return self.load_uploaded_data()

    # ------------------------------------------------------------------
    def _validate_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Remove empty dataframes from ``data``."""
        return {
            name: df
            for name, df in data.items()
            if isinstance(df, pd.DataFrame) and not df.empty
        }

    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    def _format_results(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Return final result dictionary with ``status`` key."""
        result = dict(stats)
        result["status"] = "success"
        return result

    # ------------------------------------------------------------------
    def _process_uploaded_data_directly(
        self, data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Backward compatible helper to process uploaded ``data``."""
        validated = self._validate_data(data)
        return self._calculate_statistics(validated)

    # ------------------------------------------------------------------
    def analyze_uploaded_data(self) -> Dict[str, Any]:
        """Main entry point coordinating upload analytics."""
        try:
            data = self._load_data()
            validated = self._validate_data(data)
            stats = self._calculate_statistics(validated)
            return self._format_results(stats)
        except Exception as exc:  # pragma: no cover - best effort
            return {"status": "error", "message": str(exc)}

    # ------------------------------------------------------------------
    def get_analytics_from_uploaded_data(self) -> Dict[str, Any]:
        """Load and analyze uploaded data, returning analytics summary."""
        try:
            data = self.load_uploaded_data()
            if not data:
                return {"status": "no_data", "message": "No uploaded files available"}
            result = self._process_uploaded_data_directly(data)
            result.update({"status": "success", "files_processed": len(data)})
            return result
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    # ------------------------------------------------------------------
    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a normalized copy of ``df`` removing empty rows."""
        if df is None:
            raise ValueError("No DataFrame provided")
        try:
            cleaned_df = df.dropna(how="all").copy()
            cleaned_df.columns = [
                str(col).strip().replace(" ", "_").lower() for col in cleaned_df.columns
            ]
            return cleaned_df
        except Exception as exc:
            raise ValueError(f"Failed to clean dataframe: {exc}") from exc

    # ------------------------------------------------------------------
    def _get_column_statistics(self, series: pd.Series) -> Dict[str, Any]:
        """Return basic statistics for a column."""
        stats: Dict[str, Any] = {
            "non_null": int(series.count()),
            "unique": int(series.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(series):
            stats.update(
                {
                    "min": float(series.min()) if not series.empty else None,
                    "max": float(series.max()) if not series.empty else None,
                    "mean": float(series.mean()) if not series.empty else None,
                }
            )
        return stats

    # ------------------------------------------------------------------
    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return a summary dictionary for ``df``."""
        try:
            return {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
                "null_counts": df.isnull().sum().to_dict(),
                "column_stats": {
                    col: self._get_column_statistics(df[col]) for col in df.columns
                },
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    # ------------------------------------------------------------------
    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Return uploaded data from the configured ``data_store``."""
        try:
            store = self.data_store
            if store is None:
                return {}
            if isinstance(store, dict):
                return {
                    name: df
                    for name, df in store.items()
                    if isinstance(df, pd.DataFrame)
                }
            if hasattr(store, "get_uploaded_data"):
                data = store.get_uploaded_data()  # type: ignore[attr-defined]
            elif hasattr(store, "load_uploaded_data"):
                data = store.load_uploaded_data()  # type: ignore[attr-defined]
            else:
                return {}
            if not isinstance(data, dict):
                return {}
            return {
                name: df
                for name, df in data.items()
                if isinstance(df, pd.DataFrame)
            }
        except Exception:
            return {}


__all__ = ["UploadAnalyticsProcessor"]
