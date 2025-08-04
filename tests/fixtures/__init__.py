from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

# ``UploadAnalyticsProcessor`` is intentionally imported from the lightweight
# implementation used in tests to avoid pulling in heavy optional dependencies.

class UploadAnalyticsProcessor:
    """Minimal upload analytics processor used in tests."""

    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:  # pragma: no cover - simple stub
        return {}

    def _load_data(self) -> Dict[str, pd.DataFrame]:
        return self.load_uploaded_data()

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df.copy()
        cleaned = df.dropna(how="all").copy()
        cleaned.columns = [c.strip().lower().replace(" ", "_") for c in cleaned.columns]
        cleaned = cleaned.rename(columns={"device_name": "door_id", "event_time": "timestamp"})
        if "timestamp" in cleaned.columns:
            cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp"], errors="coerce")
        return cleaned.dropna(how="all")

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
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

    def _validate_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        cleaned: Dict[str, pd.DataFrame] = {}
        for name, df in data.items():
            cleaned_df = self.clean_uploaded_dataframe(df)
            if not cleaned_df.empty:
                cleaned[name] = cleaned_df
        return cleaned

    def _calculate_statistics(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        if not data:
            return {
                "total_events": 0,
                "active_users": 0,
                "active_doors": 0,
                "date_range": {"start": "Unknown", "end": "Unknown"},
            }
        combined = pd.concat(list(data.values()), ignore_index=True)
        return self.summarize_dataframe(combined)

    def _format_results(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(stats)
        result["status"] = result.get("status", "success")
        return result

    def _process_uploaded_data_directly(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        validated = self._validate_data(data)
        return self._calculate_statistics(validated)

    def analyze_uploaded_data(self) -> Dict[str, Any]:
        data = self._load_data()
        stats = self._process_uploaded_data_directly(data)
        return self._format_results(stats)


class MockSecurityValidator:
    """Trivial security validator used for tests."""

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return ``df`` unchanged."""
        return df


class MockUploadDataStore:
    """In-memory store for uploaded dataframes."""

    def __init__(self, data: Optional[Dict[str, pd.DataFrame]] = None) -> None:
        self._data = data or {}

    def get_all_data(self) -> Dict[str, pd.DataFrame]:
        return self._data


class MockCallbackManager:
    """Collect emitted callback events for inspection."""

    def __init__(self) -> None:
        self.events: list[tuple[str, Dict[str, Any]]] = []

    def emit(self, event: str, **payload: Any) -> None:  # pragma: no cover - trivial
        self.events.append((event, payload))


class MockProcessor:
    """Processor that simply proxies data from the store."""

    def __init__(
        self,
        data_store: MockUploadDataStore,
        validator: Optional[MockSecurityValidator] = None,
        callbacks: Optional[MockCallbackManager] = None,
    ) -> None:
        self.data_store = data_store
        self.validator = validator or MockSecurityValidator()
        self.callbacks = callbacks or MockCallbackManager()

    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Return data stored in :class:`MockUploadDataStore`."""
        return self.data_store.get_all_data()


def create_test_upload_processor(
    data: Optional[Dict[str, pd.DataFrame]] = None,
) -> UploadAnalyticsProcessor:
    """Create an ``UploadAnalyticsProcessor`` wired with simple mocks."""

    store = MockUploadDataStore(data)
    validator = MockSecurityValidator()
    callbacks = MockCallbackManager()
    processor = MockProcessor(store, validator, callbacks)

    class TestUploadAnalyticsProcessor(UploadAnalyticsProcessor):
        def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:  # type: ignore[override]
            return processor.load_uploaded_data()

    return TestUploadAnalyticsProcessor()


__all__ = [
    "create_test_upload_processor",
    "MockSecurityValidator",
    "MockProcessor",
    "MockUploadDataStore",
    "MockCallbackManager",
]
