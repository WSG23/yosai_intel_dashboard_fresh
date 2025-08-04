from typing import Any, Dict, List

import pandas as pd

from yosai_intel_dashboard.src.services.upload.protocols import UploadAnalyticsProtocol


class UploadAnalyticsProcessor(UploadAnalyticsProtocol):
    """Minimal stub for tests."""

    def __init__(self, *args, **kwargs) -> None:
        pass

    # ------------------------------------------------------------------
    def _load_data(self):
        """Return uploaded data using :meth:`load_uploaded_data`."""
        return self.load_uploaded_data()

    # ------------------------------------------------------------------
    def _validate_data(self, data):
        """Remove empty dataframes from ``data``."""
        return {name: df for name, df in data.items() if not df.empty}

    # ------------------------------------------------------------------
    def _calculate_statistics(self, data):
        """Calculate basic statistics for uploaded ``data``.

        This implementation scans each DataFrame once while collecting
        unique ``Person ID`` and ``Device name`` values into dedicated
        ``users`` and ``doors`` sets. By relying on ``dropna().unique()``
        the method avoids costly per-row iteration over
        ``df.to_dict('records')``.
        """

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
    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return analytics summary for ``df``.

        Computes event counts, unique entity counts, access result
        distribution, date range and top users/doors. Missing columns and
        empty dataframes are handled gracefully.
        """

        if df.empty:
            return {
                "total_events": 0,
                "active_users": 0,
                "active_doors": 0,
                "unique_users": 0,
                "unique_doors": 0,
                "access_patterns": {},
                "date_range": {"start": "Unknown", "end": "Unknown"},
                "top_users": [],
                "top_doors": [],
            }

        total_events = len(df)

        def _unique(col: str) -> int:
            return int(df[col].nunique(dropna=True)) if col in df.columns else 0

        active_users = _unique("person_id")
        active_doors = _unique("door_id")

        access_patterns = (
            df["access_result"].value_counts().to_dict()
            if "access_result" in df.columns
            else {}
        )

        date_range = {"start": "Unknown", "end": "Unknown"}
        if "timestamp" in df.columns:
            valid_ts = pd.to_datetime(df["timestamp"], errors="coerce").dropna()
            if not valid_ts.empty:
                date_range = {
                    "start": str(valid_ts.min().date()),
                    "end": str(valid_ts.max().date()),
                }

        top_users: List[Dict[str, Any]] = []
        if "person_id" in df.columns:
            user_counts = df["person_id"].value_counts().head(10)
            top_users = [
                {"user_id": uid, "count": int(cnt)} for uid, cnt in user_counts.items()
            ]

        top_doors: List[Dict[str, Any]] = []
        if "door_id" in df.columns:
            door_counts = df["door_id"].value_counts().head(10)
            top_doors = [
                {"door_id": did, "count": int(cnt)} for did, cnt in door_counts.items()
            ]

        return {
            "total_events": total_events,
            "active_users": active_users,
            "active_doors": active_doors,
            "unique_users": active_users,
            "unique_doors": active_doors,
            "access_patterns": access_patterns,
            "date_range": date_range,
            "top_users": top_users,
            "top_doors": top_doors,
        }

    # ------------------------------------------------------------------
    def _format_results(self, stats):
        """Return final result dictionary with ``status`` key."""
        result = dict(stats)
        result["status"] = "success"
        return result

    # ------------------------------------------------------------------
    def _process_uploaded_data_directly(self, data):
        """Backward compatible helper to process uploaded ``data``."""
        validated = self._validate_data(data)
        return self._calculate_statistics(validated)

    # ------------------------------------------------------------------
    def analyze_uploaded_data(self):
        """Main entry point coordinating upload analytics."""
        try:
            data = self._load_data()
            validated = self._validate_data(data)
            stats = self._calculate_statistics(validated)
            return self._format_results(stats)
        except Exception as exc:  # pragma: no cover - best effort
            return {"status": "error", "message": str(exc)}

    def load_uploaded_data(self):  # pragma: no cover - simple stub
        return {}


__all__ = ["UploadAnalyticsProcessor"]
