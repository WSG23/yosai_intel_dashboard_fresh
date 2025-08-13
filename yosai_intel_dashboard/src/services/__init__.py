#!/usr/bin/env python3
"""Simplified Services Package"""
import logging
import os
import sys
from pathlib import Path
from types import ModuleType

try:
    from .analytics_service import AnalyticsService
except Exception:  # pragma: no cover - optional dependency fallback

    class AnalyticsService:
        """Fallback stub when analytics service is unavailable."""

        pass


if os.getenv("LIGHTWEIGHT_SERVICES"):
    __all__ = ["AnalyticsService"]
else:

    from yosai_intel_dashboard.src.core.container import container

    from .ab_testing import ModelABTester
    from .ai_mapping_store import ai_mapping_store
    from .analytics.calculator import Calculator
    from .analytics.data.loader import DataLoader
    from .analytics.generator import AnalyticsGenerator
    from .analytics.processor import AnalyticsProcessor
    from .async_file_processor import AsyncFileProcessor
    from .chunked_analysis import analyze_with_chunking
    from .controllers.upload_controller import UploadProcessingController
    from .data_loading_service import DataLoadingService
    from .data_processing.file_handler import FileHandler
    from .data_processing.processor import Processor
    from .data_processing_service import DataProcessingService
    from .database_retriever import DatabaseAnalyticsRetriever
    from .db_analytics_helper import DatabaseAnalyticsHelper
    from .explainability_service import ExplainabilityService
    from .helpers.database_initializer import initialize_database
    from .microservices_architect import MicroservicesArchitect, ServiceBoundary
    from .publishing_service import PublishingService
    from .query_optimizer import QueryOptimizer
    from .report_generation_service import ReportGenerationService
    from .result_formatting import (
        apply_regular_analysis,
        calculate_temporal_stats_safe,
        prepare_regular_result,
        regular_analysis,
    )
    from .summary_report_generator import SummaryReportGenerator
    from .summary_reporter import SummaryReporter
    from .upload_processing import UploadAnalyticsProcessor

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

    # Resolve optional services from the container
    FileHandlerService = (
        container.get("FileHandler") if container.has("FileHandler") else None
    )
    FILE_HANDLER_AVAILABLE = FileHandlerService is not None

    create_analytics_service = (
        container.get("create_analytics_service")
        if container.has("create_analytics_service")
        else None
    )
    AnalyticsService = (
        container.get("AnalyticsService") if container.has("AnalyticsService") else None
    )

    def get_analytics_service():
        """Return a shared :class:`AnalyticsService` instance if available."""
        getter = (
            container.get("get_analytics_service")
            if container.has("get_analytics_service")
            else None
        )
        if getter is None:
            return None
        try:
            return getter()
        except Exception as exc:  # pragma: no cover - best effort
            logger.exception("Failed to initialize AnalyticsService: %s", exc)
            return None

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
        "AsyncFileProcessor",
        "DatabaseAnalyticsHelper",
        "SummaryReporter",
        "DatabaseAnalyticsRetriever",
        "SummaryReportGenerator",
        "DataLoader",
        "Calculator",
        "DataLoadingService",
        "DataProcessingService",
        "ReportGenerationService",
        "PublishingService",
        "AnalyticsProcessor",
        "MicroservicesArchitect",
        "ServiceBoundary",
        "ModelABTester",
        "ExplainabilityService",
        "QueryOptimizer",
    ]
