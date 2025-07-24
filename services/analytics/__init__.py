"""Analytics Domain Public API."""

from .calculator import Calculator
from .data_loader import DataLoader
from .metrics_calculator import MetricsCalculator
from .preparation import prepare_dataframe
from .protocols import (
    AnalyticsServiceProtocol,
    DataProcessorProtocol,
    MetricsCalculatorProtocol,
    ReportGeneratorProtocol,
)
from .publisher import Publisher
from .upload_analytics import (
    UploadAnalyticsProcessor,
    run_anomaly_detection,
    summarize_dataframes,
)

__all__ = [
    "AnalyticsServiceProtocol",
    "DataProcessorProtocol",
    "ReportGeneratorProtocol",
    "MetricsCalculatorProtocol",
    "summarize_dataframes",
    "run_anomaly_detection",
    "UploadAnalyticsProcessor",
    "prepare_dataframe",
    "MetricsCalculator",
    "DataLoader",
    "Calculator",
    "Publisher",
]
