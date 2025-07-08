"""Analytics domain protocols."""
from abc import abstractmethod
from typing import Any, Dict, List, Protocol, runtime_checkable
import pandas as pd


@runtime_checkable
class DataProcessorProtocol(Protocol):
    """Protocol for data processing operations."""

    @abstractmethod
    def process_dataframe(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Process DataFrame according to configuration."""
        ...

    @abstractmethod
    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate data quality and return metrics."""
        ...


@runtime_checkable
class ReportGeneratorProtocol(Protocol):
    """Protocol for report generation."""

    @abstractmethod
    def generate_summary_report(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary report from data."""
        ...

    @abstractmethod
    def generate_detailed_report(self, data: pd.DataFrame, template: str) -> str:
        """Generate detailed report using template."""
        ...
