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
from .timescale_queries import (
    build_sliding_window_query,
    build_time_bucket_query,
    fetch_sliding_window,
    fetch_time_buckets,
)
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
    "build_time_bucket_query",
    "build_sliding_window_query",
    "fetch_time_buckets",
    "fetch_sliding_window",
]
