"""Analytics Domain Public API."""

from .async_service import AsyncAnalyticsService, PGAnalyticsRepository
from .calculator import Calculator, create_calculator
from .data_loader import DataLoader, create_loader
from .metrics_calculator import MetricsCalculator
from .preparation import prepare_dataframe
from .protocols import (
    AnalyticsServiceProtocol,
    DataProcessorProtocol,
    MetricsCalculatorProtocol,
    ReportGeneratorProtocol,
)
from .publisher import Publisher
from .orchestrator import AnalyticsOrchestrator

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
    "create_loader",
    "Calculator",
    "create_calculator",
    "Publisher",
    "create_publisher",
    "build_time_bucket_query",
    "build_sliding_window_query",
    "fetch_time_buckets",
    "fetch_sliding_window",
    "AsyncAnalyticsService",
    "PGAnalyticsRepository",
    "AnalyticsOrchestrator",
]
