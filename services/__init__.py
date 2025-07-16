#!/usr/bin/env python3
"""Simplified Services Package"""
import logging

from .ai_mapping_store import ai_mapping_store
from .analytics.upload_analytics import UploadAnalyticsProcessor
from .analytics_generator import AnalyticsGenerator
from .chunked_analysis import analyze_with_chunking
from .data_processing.processor import Processor
from .data_processing.unified_file_validator import UnifiedFileValidator
from .db_analytics_helper import DatabaseAnalyticsHelper
from .registry import get_service
from .result_formatting import (
    apply_regular_analysis,
    calculate_temporal_stats_safe,
    prepare_regular_result,
    regular_analysis,
)
from .summary_reporter import SummaryReporter
from .data_loader import DataLoader
from .analytics_processor import AnalyticsProcessor

logger = logging.getLogger(__name__)

# Resolve optional services from the registry
UnifiedFileValidatorService = get_service("UnifiedFileValidator")
FILE_VALIDATOR_AVAILABLE = UnifiedFileValidatorService is not None


get_analytics_service = get_service("get_analytics_service")
create_analytics_service = get_service("create_analytics_service")
AnalyticsService = get_service("AnalyticsService")
ANALYTICS_SERVICE_AVAILABLE = AnalyticsService is not None

__all__ = [
    "UnifiedFileValidator",
    "FILE_VALIDATOR_AVAILABLE",
    "get_analytics_service",
    "create_analytics_service",
    "AnalyticsService",
    "ANALYTICS_SERVICE_AVAILABLE",
    "AnalyticsGenerator",
    "Processor",
    "analyze_with_chunking",
    "prepare_regular_result",
    "apply_regular_analysis",
    "calculate_temporal_stats_safe",
    "regular_analysis",
    "ai_mapping_store",
    "UploadAnalyticsProcessor",
    "DatabaseAnalyticsHelper",
    "SummaryReporter",
    "DataLoader",
    "AnalyticsProcessor",
]
