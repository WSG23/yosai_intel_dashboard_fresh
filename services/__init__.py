#!/usr/bin/env python3
"""Simplified Services Package"""
import logging

from .ai_mapping_store import ai_mapping_store
from .data_loader import DataLoader
from .data_validation import DataValidationService
from .analytics_generator import AnalyticsGenerator
from .data_loading_service import DataLoadingService
from .data_processing.processor import Processor
from .chunked_analysis import analyze_with_chunking
from .result_formatting import (
    prepare_regular_result,
    apply_regular_analysis,
    calculate_temporal_stats_safe,
    regular_analysis,
)
from .registry import get_service
from .db_analytics_helper import DatabaseAnalyticsHelper
from .summary_reporting import SummaryReporter
from .analytics import analyze_uploaded_data
from .data_processing.file_handler import FileHandler

logger = logging.getLogger(__name__)

# Resolve optional services from the registry
FileHandlerService = get_service("FileHandler")
FILE_HANDLER_AVAILABLE = FileHandlerService is not None

get_analytics_service = get_service("get_analytics_service")
create_analytics_service = get_service("create_analytics_service")
AnalyticsService = get_service("AnalyticsService")
ANALYTICS_SERVICE_AVAILABLE = AnalyticsService is not None

__all__ = [
    "FileHandler",
    "FILE_HANDLER_AVAILABLE",
    "get_analytics_service",
    "create_analytics_service",
    "AnalyticsService",
    "ANALYTICS_SERVICE_AVAILABLE",
    "DataLoader",
    "DataValidationService",
    "AnalyticsGenerator",
    "DataLoadingService",
    "Processor",
    "analyze_with_chunking",
    "prepare_regular_result",
    "apply_regular_analysis",
    "calculate_temporal_stats_safe",
    "regular_analysis",
    "ai_mapping_store",
    "DatabaseAnalyticsHelper",
    "SummaryReporter",
    "analyze_uploaded_data",
    "FileHandler",
]
