from __future__ import annotations

"""Protocol definitions for analytics services."""

from typing import Any, Dict, List, Protocol

from shared.events.names import EventName

import pandas as pd


class LoaderProtocol(Protocol):
    """Load and prepare raw analytics data."""

    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]: ...

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame: ...

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]: ...

    def load_patterns_dataframe(
        self, data_source: str | None
    ) -> tuple[pd.DataFrame, int]: ...


class ValidatorProtocol(Protocol):
    """Validate uploaded content."""

    def validate_input(
        self, value: str, field_name: str = "input"
    ) -> Dict[str, Any]: ...

    def validate_file_upload(self, filename: str, content: bytes) -> Dict[str, Any]: ...


class TransformerProtocol(Protocol):
    """Transform dataframes for analytics."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame: ...

    def diagnose(self, df: pd.DataFrame) -> Dict[str, Any]: ...


class CalculatorProtocol(Protocol):
    """Perform metrics calculations."""

    def calculate_stats(self, df: pd.DataFrame) -> tuple[int, int, int, int]: ...

    def analyze_users(
        self, df: pd.DataFrame, unique_users: int
    ) -> tuple[list[str], list[str], list[str]]: ...

    def analyze_devices(
        self, df: pd.DataFrame, unique_devices: int
    ) -> tuple[list[str], list[str], list[str]]: ...

    def log_analysis_summary(self, result_total: int, original_rows: int) -> None: ...

    def analyze_patterns(
        self, df: pd.DataFrame, original_rows: int
    ) -> Dict[str, Any]: ...


class AggregatorProtocol(Protocol):
    """Aggregate dataframe metrics."""

    def aggregate(
        self, df: pd.DataFrame, groupby: List[str], metrics: List[str]
    ) -> pd.DataFrame: ...


class AnalyzerProtocol(Protocol):
    """Analyze prepared data for patterns."""

    def analyze(self, df: pd.DataFrame, original_rows: int) -> Dict[str, Any]: ...


class RepositoryProtocol(Protocol):
    """Access analytics data from a persistence layer."""

    def get_analytics(self) -> Dict[str, Any]: ...


class CacheProtocol(Protocol):
    """Provide caching helpers."""

    def cache(self, name: str, ttl: int) -> Any: ...


class PersistenceProtocol(Protocol):
    """Initialize persistence resources."""

    def initialize(self, database: Any | None) -> tuple[Any | None, Any, Any]: ...


class EventPublisherProtocol(Protocol):
    """Publish analytics events."""

    def publish(
        self, payload: Dict[str, Any], event: str = EventName.ANALYTICS_UPDATE
    ) -> None: ...


class EventSubscriberProtocol(Protocol):
    """Subscribe to analytics events."""

    def subscribe(self, event: str, handler: Any) -> None: ...
