from services.upload.protocols import UploadAnalyticsProtocol


class UploadAnalyticsProcessor(UploadAnalyticsProtocol):
    """Minimal stub for tests."""

    def __init__(self, *args, **kwargs) -> None:
        pass

    def _process_uploaded_data_directly(self, data):
        return {
            "total_events": sum(len(df) for df in data.values()),
            "active_users": len({row['Person ID'] for df in data.values() for row in df.to_dict('records')}),
            "active_doors": len({row['Device name'] for df in data.values() for row in df.to_dict('records')}),
        }

    def analyze_uploaded_data(self):
        data = self.load_uploaded_data()
        metrics = self._process_uploaded_data_directly(data)
        metrics["status"] = "success"
        return metrics

    def load_uploaded_data(self):  # pragma: no cover - simple stub
        return {}
