from typing import Any, Dict

import pandas as pd

from yosai_intel_dashboard.src.services.upload.protocols import (
    UploadAnalyticsProtocol,
)


class UploadAnalyticsProcessor(UploadAnalyticsProtocol):
    """Process and analyze uploaded access control data."""

    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - simple stub
        pass

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def get_analytics_from_uploaded_data(self) -> Dict[str, Any]:
        """Load uploaded data and return aggregated analytics."""
        try:
            data = self._load_data()
            stats = self._process_uploaded_data_directly(data)
            return self._format_results(stats)
        except Exception as exc:  # pragma: no cover - best effort
            return {"status": "error", "message": str(exc)}

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop empty rows and normalize column names in ``df``."""
        if df.empty:
            return df.copy()

        cleaned = df.dropna(how="all").copy()
        cleaned.columns = [c.strip().lower().replace(" ", "_") for c in cleaned.columns]
        cleaned = cleaned.rename(columns={"device_name": "door_id", "event_time": "timestamp"})
        if "timestamp" in cleaned.columns:
            cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp"], errors="coerce")
        return cleaned.dropna(how="all")

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return basic statistics for ``df``."""

        total_events = len(df)
        active_users = df["person_id"].nunique() if "person_id" in df.columns else 0
        active_doors = df["door_id"].nunique() if "door_id" in df.columns else 0

        date_range = {"start": "Unknown", "end": "Unknown"}
        if "timestamp" in df.columns:
            ts = pd.to_datetime(df["timestamp"], errors="coerce").dropna()
            if not ts.empty:
                date_range = {"start": str(ts.min().date()), "end": str(ts.max().date())}


        return {
            "total_events": int(total_events),
            "active_users": int(active_users),
            "active_doors": int(active_doors),
            "date_range": date_range,
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
            return {"total_events": 0, "active_users": 0, "active_doors": 0, "date_range": {"start": "Unknown", "end": "Unknown"}}

        combined = pd.concat(list(data.values()), ignore_index=True)
        return self.summarize_dataframe(combined)

    def _format_results(self, stats: Dict[str, Any]) -> Dict[str, Any]:

        """Return final result dictionary with ``status`` key."""
        result = dict(stats)
        result["status"] = result.get("status", "success")
        return result

    # ------------------------------------------------------------------
    def _process_uploaded_data_directly(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:

        """Backward compatible helper to process uploaded ``data``."""
        validated = self._validate_data(data)
        return self._calculate_statistics(validated)

    # ------------------------------------------------------------------
    def analyze_uploaded_data(self) -> Dict[str, Any]:
        """Backward compatible wrapper around :meth:`get_analytics_from_uploaded_data`."""
        return self.get_analytics_from_uploaded_data()

    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:  # pragma: no cover - simple stub
        return {}



# Expose commonly used methods at module level for convenience
get_analytics_from_uploaded_data = UploadAnalyticsProcessor.get_analytics_from_uploaded_data
clean_uploaded_dataframe = UploadAnalyticsProcessor.clean_uploaded_dataframe
summarize_dataframe = UploadAnalyticsProcessor.summarize_dataframe

__all__ = [
    "UploadAnalyticsProcessor",
    "get_analytics_from_uploaded_data",
    "clean_uploaded_dataframe",
    "summarize_dataframe",
]
