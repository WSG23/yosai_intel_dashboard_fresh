from typing import Any

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
