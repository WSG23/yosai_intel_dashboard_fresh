"""Analytics Domain Public API."""

from .protocols import (
    AnalyticsServiceProtocol,
    DataProcessorProtocol,
    ReportGeneratorProtocol,
    MetricsCalculatorProtocol,
)
from .upload_analytics import (
    summarize_dataframes,
    run_anomaly_detection,
    UploadAnalyticsProcessor,
)
from .preparation import prepare_dataframe
from .metrics_calculator import MetricsCalculator

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
]
