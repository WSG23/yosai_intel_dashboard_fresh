"""Analytics domain protocol definitions."""

from abc import abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class AnalyticsServiceProtocol(Protocol):
    """Protocol for analytics service operations."""

    @abstractmethod
    def get_dashboard_summary(self, time_range: str = "30d") -> Dict[str, Any]:
        """Get dashboard summary statistics."""
        ...

    @abstractmethod
    def analyze_access_patterns(
        self, days: int, user_id: str | None = None
    ) -> Dict[str, Any]:
        """Analyze access patterns over specified days."""
        ...

    @abstractmethod
    def detect_anomalies(
        self, data: pd.DataFrame, sensitivity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in access data."""
        ...

    @abstractmethod
    def generate_report(
        self, report_type: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate analytics report of specified type."""
        ...

    @abstractmethod
    def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user activity summary."""
        ...

    @abstractmethod
    def get_facility_statistics(self, facility_id: str | None = None) -> Dict[str, Any]:
        """Get facility access statistics."""
        ...


@runtime_checkable
class DataProcessorProtocol(Protocol):
    """Protocol for data processing operations."""

    @abstractmethod
    def process_access_events(self, events: pd.DataFrame) -> pd.DataFrame:
        """Process raw access events data."""
        ...

    @abstractmethod
    def clean_data(
        self, data: pd.DataFrame, rules: Dict[str, Any] | None = None
    ) -> pd.DataFrame:
        """Clean and normalize data."""
        ...

    @abstractmethod
    def aggregate_data(
        self, data: pd.DataFrame, groupby: List[str], metrics: List[str]
    ) -> pd.DataFrame:
        """Aggregate data by specified dimensions."""
        ...

    @abstractmethod
    def validate_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Validate data quality and return metrics."""
        ...

    @abstractmethod
    def enrich_data(
        self, data: pd.DataFrame, enrichment_sources: List[str]
    ) -> pd.DataFrame:
        """Enrich data with additional information."""
        ...


@runtime_checkable
class ReportGeneratorProtocol(Protocol):
    """Protocol for report generation."""

    @abstractmethod
    def generate_summary_report(
        self, data: pd.DataFrame, template: str = "default"
    ) -> Dict[str, Any]:
        """Generate summary report from data."""
        ...

    @abstractmethod
    def generate_detailed_report(self, data: pd.DataFrame, format: str = "html") -> str:
        """Generate detailed report in specified format."""
        ...

    @abstractmethod
    def generate_trend_analysis(
        self, data: pd.DataFrame, time_column: str
    ) -> Dict[str, Any]:
        """Generate trend analysis report."""
        ...

    @abstractmethod
    def export_report(
        self, report_data: Dict[str, Any], format: str, filename: str
    ) -> str:
        """Export report to file in specified format."""
        ...


@runtime_checkable
class MetricsCalculatorProtocol(Protocol):
    """Protocol for metrics calculation."""

    @abstractmethod
    def calculate_access_metrics(self, events: pd.DataFrame) -> Dict[str, float]:
        """Calculate access-related metrics."""
        ...

    @abstractmethod
    def calculate_security_metrics(self, events: pd.DataFrame) -> Dict[str, float]:
        """Calculate security-related metrics."""
        ...

    @abstractmethod
    def calculate_performance_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate performance metrics."""
        ...

    @abstractmethod
    def calculate_trend_metrics(
        self, data: pd.DataFrame, window: str = "7d"
    ) -> Dict[str, Any]:
        """Calculate trend metrics over time window."""
        ...
