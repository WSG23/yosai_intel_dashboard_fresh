#!/usr/bin/env python3
"""Simplified Services Package"""
import logging
import os
import sys
from pathlib import Path
from types import ModuleType

if os.getenv("LIGHTWEIGHT_SERVICES"):
    __all__ = []
else:

    from .ab_testing import ModelABTester
    from .ai_mapping_store import ai_mapping_store
    from .analytics.calculator import Calculator
    from .analytics.data_loader import DataLoader
    from .analytics.publisher import Publisher
    from .analytics.upload_analytics import UploadAnalyticsProcessor
    from .analytics_generator import AnalyticsGenerator
    from .analytics_processor import AnalyticsProcessor
    from .async_file_processor import AsyncFileProcessor
    from .chunked_analysis import analyze_with_chunking
    from .controllers.upload_controller import UploadProcessingController
    from .data_processing.processor import Processor
    from .data_processing.file_handler import FileHandler
    from .database_retriever import DatabaseAnalyticsRetriever
    from .db_analytics_helper import DatabaseAnalyticsHelper
    from .event_publisher import publish_event
    from .explainability_service import ExplainabilityService
    from .helpers.database_initializer import initialize_database
    from .microservices_architect import MicroservicesArchitect, ServiceBoundary
    from .registry import get_service
    from .result_formatting import (
        apply_regular_analysis,
        calculate_temporal_stats_safe,
        prepare_regular_result,
        regular_analysis,
    )
    from .summary_report_generator import SummaryReportGenerator
    from .summary_reporter import SummaryReporter

    logger = logging.getLogger(__name__)

    # Expose optional compliance services if the plugin is available
    plugin_compliance_path = (
        Path(__file__).resolve().parent
        / ".."
        / "plugins"
        / "compliance_plugin"
        / "services"
    ).resolve()
    if plugin_compliance_path.is_dir():
        module_name = __name__ + ".compliance"
        compliance_pkg = ModuleType(module_name)
        compliance_pkg.__path__ = [str(plugin_compliance_path)]
        sys.modules[module_name] = compliance_pkg
    else:  # pragma: no cover - optional dependency
        compliance_pkg = None

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
        "AnalyticsGenerator",
        "Processor",
        "analyze_with_chunking",
        "prepare_regular_result",
        "apply_regular_analysis",
        "calculate_temporal_stats_safe",
        "regular_analysis",
        "ai_mapping_store",
        "UploadAnalyticsProcessor",
        "UploadProcessingController",
        "initialize_database",
        "publish_event",
        "AsyncFileProcessor",
        "DatabaseAnalyticsHelper",
        "SummaryReporter",
        "DatabaseAnalyticsRetriever",
        "SummaryReportGenerator",
        "DataLoader",
        "Calculator",
        "Publisher",
        "AnalyticsProcessor",
        "MicroservicesArchitect",
        "ServiceBoundary",
        "ModelABTester",
        "ExplainabilityService",
    ]
