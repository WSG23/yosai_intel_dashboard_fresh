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
        """Calculate basic statistics for uploaded ``data``."""
        total_events = sum(len(df) for df in data.values())
        unique_users = {
            row.get("Person ID")
            for df in data.values()
            for row in df.to_dict("records")
            if "Person ID" in row
        }
        unique_doors = {
            row.get("Device name")
            for df in data.values()
            for row in df.to_dict("records")
            if "Device name" in row
        }
        return {
            "total_events": total_events,
            "active_users": len(unique_users),
            "active_doors": len(unique_doors),
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
