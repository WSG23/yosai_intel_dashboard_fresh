#!/usr/bin/env python3
"""Analytics Service - Enhanced with Unique Patterns Analysis.

Uploaded files are validated with
``services.data_processing.unified_file_validator.UnifiedFileValidator`` before
processing to ensure they are present, non-empty and within the configured size
limits.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Protocol

try:
    from typing import override
except ImportError:  # pragma: no cover - for Python <3.12
    from typing_extensions import override

import pandas as pd

from config.dynamic_config import dynamic_config
from core.cache_manager import CacheConfig, InMemoryCacheManager, cache_with_lock
from core.protocols import (
    AnalyticsServiceProtocol,
    ConfigurationProtocol,
    DatabaseProtocol,
    EventBusProtocol,
    StorageProtocol,
)
from models.ml import ModelRegistry
from services.analytics.calculator import Calculator, create_calculator
from services.analytics.data_loader import DataLoader, create_loader
from services.analytics.protocols import DataProcessorProtocol
from services.analytics.publisher import Publisher, create_publisher
from services.analytics.orchestrator import AnalyticsOrchestrator
from services.database_retriever import DatabaseAnalyticsRetriever

from services.analytics_summary import generate_sample_analytics
from services.controllers.upload_controller import UploadProcessingController
from services.data_processing.processor import Processor
from services.helpers.database_initializer import initialize_database
from services.database_retriever import DatabaseAnalyticsRetriever
from services.interfaces import get_upload_data_service
from services.summary_report_generator import SummaryReportGenerator
from services.upload_data_service import UploadDataService
from validation.security_validator import SecurityValidator

_cache_manager = InMemoryCacheManager(CacheConfig())


class ConfigProviderProtocol(Protocol):
    """Provide configuration values to services."""

    def get_database_config(self) -> Any:
        """Return the database configuration."""
        ...


class AnalyticsProviderProtocol(Protocol):
    """Basic analytics provider interface."""

    @override
    def process_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process ``df`` and return analytics metrics."""
        ...

    @override
    def get_metrics(self) -> Dict[str, Any]:
        """Return current analytics metrics."""
        ...


def ensure_analytics_config():
    """Emergency fix to ensure analytics configuration exists."""
    try:
        from config.dynamic_config import dynamic_config

        if not hasattr(dynamic_config, "analytics"):
            from config.constants import AnalyticsConstants

            dynamic_config.analytics = AnalyticsConstants()
    except (ImportError, AttributeError) as exc:
        logger.error(f"Failed to ensure analytics configuration: {exc}")


logger = logging.getLogger(__name__)

ensure_analytics_config()

# Thresholds used for row count sanity checks
ROW_LIMIT_WARNING = dynamic_config.analytics.row_limit_warning
"""Warning threshold when exactly 150 rows are returned."""

LARGE_DATA_THRESHOLD = dynamic_config.analytics.large_data_threshold
"""Row count above which data is considered large."""


class AnalyticsService(AnalyticsServiceProtocol):
    """Analytics service implementing ``AnalyticsServiceProtocol``."""

    def __init__(
        self,
        database: DatabaseProtocol | None = None,
        data_processor: DataProcessorProtocol | None = None,
        config: ConfigurationProtocol | None = None,
        event_bus: EventBusProtocol | None = None,
        storage: StorageProtocol | None = None,
        upload_data_service: UploadDataService | None = None,
        model_registry: ModelRegistry | None = None,
        *,
        loader: DataLoader | None = None,
        calculator: Calculator | None = None,
        publisher: Publisher | None = None,
        report_generator: SummaryReportGenerator | None = None,
        db_retriever: DatabaseAnalyticsRetriever | None = None,
    ):
        self.database = database
        self.data_processor = data_processor or Processor(
            validator=SecurityValidator()
        )
        self.config = config
        self.event_bus = event_bus
        self.storage = storage
        self.upload_data_service = upload_data_service or get_upload_data_service()
        self.model_registry = model_registry
        self.validation_service = SecurityValidator()
        if data_processor is None:
            self.processor = Processor(validator=self.validation_service)
            self.data_processor = self.processor
        else:
            self.processor = data_processor
            self.data_processor = data_processor
        # Legacy attribute aliases
        self.data_loading_service = self.processor
        from services.data_processing.unified_file_validator import UnifiedFileValidator
        self.file_handler = UnifiedFileValidator()

        self.upload_controller = UploadProcessingController(
            self.validation_service,
            self.processor,
            self.upload_data_service,
        )
        self.upload_processor = self.upload_controller.upload_processor
        self.report_generator = report_generator or SummaryReportGenerator()
        self._setup_database(db_retriever)
        self._create_orchestrator(loader, calculator, publisher)


    def _setup_database(
        self, db_retriever: DatabaseAnalyticsRetriever | None = None
    ) -> None:
        """Initialize database helpers and retriever."""
        (
            self.database_manager,
            self.db_helper,
            self.summary_reporter,
        ) = initialize_database(self.database)
        self.database_retriever = db_retriever or DatabaseAnalyticsRetriever(
            self.db_helper
        )

    def _create_orchestrator(
        self,
        loader: DataLoader | None,
        calculator: Calculator | None,
        publisher: Publisher | None,
    ) -> None:
        """Set up loader, calculator, publisher and orchestrator."""
        self.data_loader = loader or DataLoader(
            self.upload_controller, self.processor
        )
        self.calculator = calculator or Calculator(self.report_generator)
        self.publisher = publisher or Publisher(self.event_bus)
        self.orchestrator = AnalyticsOrchestrator(
            self.data_loader,
            self.validation_service,
            self.processor,
            self.database_retriever,
            self.publisher,
        )

    def get_analytics_from_uploaded_data(self) -> Dict[str, Any]:
        """Process uploaded files via orchestrator."""
        return self.orchestrator.process_uploaded_data()

    def get_analytics_by_source(self, source: str) -> Dict[str, Any]:
        """Get analytics from specified source with forced uploaded data check"""

        # FORCE CHECK: If uploaded data exists, use it regardless of source
        try:
            uploaded_data = self.load_uploaded_data()

            if uploaded_data and source in ["uploaded", "sample"]:
                logger.info(f"Forcing uploaded data usage (source was: {source})")
                return self._process_uploaded_data_directly(uploaded_data)

        except (ImportError, FileNotFoundError, OSError, RuntimeError) as e:
            logger.error(f"Uploaded data check failed: {e}", exc_info=True)
        except Exception:
            logger.exception("Unexpected error during uploaded data check")
            raise

        # Original logic for when no uploaded data
        if source == "sample":
            return generate_sample_analytics()
        elif source == "uploaded":
            return {"status": "no_data", "message": "No uploaded files available"}
        elif source == "database":
            return self._get_database_analytics()
        else:
            return {"status": "error", "message": f"Unknown source: {source}"}

    def _process_uploaded_data_directly(
        self, uploaded_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process uploaded files using chunked streaming."""
        return self.orchestrator.process_uploaded_data_directly(uploaded_data)

    async def aprocess_uploaded_data_directly(
        self, uploaded_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Asynchronously process uploaded files."""
        return await self.orchestrator.aprocess_uploaded_data_directly(uploaded_data)

    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Load uploaded data from the file upload page."""
        return self.data_loader.load_uploaded_data()

    async def aload_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Asynchronously load uploaded data."""
        return await asyncio.to_thread(self.data_loader.load_uploaded_data)

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply standard column mappings and basic cleaning."""
        return self.data_loader.clean_uploaded_dataframe(df)

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create a summary dictionary from a combined DataFrame."""
        return self.data_loader.summarize_dataframe(df)

    async def asummarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Asynchronously summarize a dataframe."""
        return await asyncio.to_thread(self.data_loader.summarize_dataframe, df)

    def analyze_with_chunking(
        self, df: pd.DataFrame, analysis_types: List[str]
    ) -> Dict[str, Any]:
        """Analyze a DataFrame using chunked processing."""
        return self.data_loader.analyze_with_chunking(df, analysis_types)

    async def aanalyze_with_chunking(
        self, df: pd.DataFrame, analysis_types: List[str]
    ) -> Dict[str, Any]:
        """Asynchronously analyze a DataFrame using chunked processing."""
        return await asyncio.to_thread(
            self.data_loader.analyze_with_chunking, df, analysis_types
        )

    def diagnose_data_flow(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Diagnostic method to check data processing flow."""
        return self.data_loader.diagnose_data_flow(df)

    async def adiagnose_data_flow(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Asynchronously diagnose data processing flow."""
        return await asyncio.to_thread(self.data_loader.diagnose_data_flow, df)

    def _get_real_uploaded_data(self) -> Dict[str, Any]:
        """Load and summarize all uploaded records."""
        return self.data_loader.get_real_uploaded_data()

    async def _aget_real_uploaded_data(self) -> Dict[str, Any]:
        """Asynchronously load all uploaded records."""
        return await asyncio.to_thread(self.data_loader.get_real_uploaded_data)

    def _get_analytics_with_fixed_processor(self) -> Dict[str, Any]:
        """Get analytics using the sample file processor."""
        return self.data_loader.get_analytics_with_fixed_processor()

    async def _aget_analytics_with_fixed_processor(self) -> Dict[str, Any]:
        """Asynchronously get analytics using the sample file processor."""
        return await asyncio.to_thread(
            self.data_loader.get_analytics_with_fixed_processor
        )

    @cache_with_lock(_cache_manager, ttl=600)
    def _get_database_analytics(self) -> Dict[str, Any]:
        """Get analytics from database."""
        return self.orchestrator.get_database_analytics()

    async def _aget_database_analytics(self) -> Dict[str, Any]:
        """Asynchronously get analytics from database."""
        return await asyncio.to_thread(self.orchestrator.get_database_analytics)

    @cache_with_lock(_cache_manager, ttl=300)
    @override
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get a basic dashboard summary"""
        try:
            return self.orchestrator.process_uploaded_data()

        except RuntimeError as e:
            logger.error(f"Dashboard summary failed: {e}")
            return {"status": "error", "message": str(e)}

    def _publish_event(
        self, payload: Dict[str, Any], event: str = "analytics_update"
    ) -> None:
        """Publish ``payload`` to the event bus if available."""
        self.publisher.publish(payload, event)

    def _load_patterns_dataframe(
        self, data_source: str | None
    ) -> tuple[pd.DataFrame, int]:
        """Return dataframe and original row count for pattern analysis."""
        return self.data_loader.load_patterns_dataframe(data_source)

    async def _aload_patterns_dataframe(
        self, data_source: str | None
    ) -> tuple[pd.DataFrame, int]:
        """Asynchronously load dataframe for pattern analysis."""
        return await asyncio.to_thread(
            self.data_loader.load_patterns_dataframe, data_source
        )

    # ------------------------------------------------------------------
    # Pattern analysis helpers
    # ------------------------------------------------------------------
    def _calculate_stats(self, df: pd.DataFrame) -> tuple[int, int, int, int]:
        """Return basic statistics for pattern analysis."""
        return self.calculator.calculate_stats(df)

    def _analyze_users(
        self, df: pd.DataFrame, unique_users: int
    ) -> tuple[list[str], list[str], list[str]]:
        """Return user activity groupings."""
        return self.calculator.analyze_users(df, unique_users)

    def _analyze_devices(
        self, df: pd.DataFrame, unique_devices: int
    ) -> tuple[list[str], list[str], list[str]]:
        """Return device activity groupings."""
        return self.calculator.analyze_devices(df, unique_devices)

    def _log_analysis_summary(self, result_total: int, original_rows: int) -> None:
        """Log summary details after pattern analysis."""
        self.calculator.log_analysis_summary(result_total, original_rows)

    def _analyze_patterns(self, df: pd.DataFrame, original_rows: int) -> Dict[str, Any]:
        """Run the unique patterns analysis on ``df``."""
        return self.calculator.analyze_patterns(df, original_rows)

    @cache_with_lock(_cache_manager, ttl=600)
    def get_unique_patterns_analysis(
        self, data_source: str | None = None
    ) -> Dict[str, Any]:
        """Get unique patterns analysis for the requested source."""
        logger = logging.getLogger(__name__)

        try:
            logger.info("🎯 Starting Unique Patterns Analysis")
            return self.orchestrator.get_unique_patterns_analysis(data_source)
        except RuntimeError as e:
            logger.error(f"❌ Unique patterns analysis failed: {e}")
            return {
                "status": "error",
                "message": f"Unique patterns analysis failed: {str(e)}",
                "data_summary": {"total_records": 0},
            }

    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        return self.summary_reporter.health_check()

    def get_data_source_options(self) -> List[Dict[str, str]]:
        """Get available data source options"""
        return self.summary_reporter.get_data_source_options()

    def get_available_sources(self) -> list[str]:
        """Return identifiers for available data sources."""
        return self.summary_reporter.get_available_sources()

    def get_date_range_options(self) -> Dict[str, str]:
        """Get default date range options"""
        return self.summary_reporter.get_date_range_options()

    def get_analytics_status(self) -> Dict[str, Any]:
        """Get current analytics status"""
        return self.summary_reporter.get_analytics_status()

    # ------------------------------------------------------------------
    # AnalyticsProviderProtocol implementation
    # ------------------------------------------------------------------
    @override
    def process_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Alias for :meth:`process_data` required by ``AnalyticsProviderProtocol``."""
        return self.process_data(df)

    @override
    def process_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process ``df`` and return a metrics dictionary."""
        cleaned = self.clean_uploaded_dataframe(df)
        return self.summarize_dataframe(cleaned)

    @override
    def get_metrics(self) -> Dict[str, Any]:
        """Return current analytics metrics."""
        return self.get_analytics_status()

    # ------------------------------------------------------------------
    # Placeholder implementations for abstract methods
    # ------------------------------------------------------------------
    @override
    def analyze_access_patterns(
        self, days: int, user_id: str | None = None
    ) -> Dict[str, Any]:
        """Analyze access patterns over the given timeframe."""
        logger.debug(
            f"analyze_access_patterns called with days={days} user_id={user_id}"
        )
        return {"patterns": [], "days": days, "user_id": user_id}

    @override
    def detect_anomalies(
        self, data: pd.DataFrame, sensitivity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in the provided data."""
        logger.debug(f"detect_anomalies called with sensitivity={sensitivity}")
        return []

    @override
    def generate_report(
        self, report_type: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate an analytics report."""
        logger.debug(
            f"generate_report called with report_type={report_type} params={params}"
        )
        return {"report_type": report_type, "params": params}

    # ------------------------------------------------------------------
    def load_model_from_registry(
        self, name: str, *, destination_dir: str | None = None
    ) -> str | None:
        """Download the active model from the registry."""
        if self.model_registry is None:
            return None
        record = self.model_registry.get_model(name, active_only=True)
        if record is None:
            return None
        dest = Path(destination_dir or dynamic_config.analytics.ml_models_path)
        dest = dest / name / record.version
        dest.mkdir(parents=True, exist_ok=True)
        local_path = dest / os.path.basename(record.storage_uri)
        try:
            self.model_registry.download_artifact(record.storage_uri, str(local_path))
            return str(local_path)
        except Exception:  # pragma: no cover - best effort
            logger.exception(f"Failed to download model {name}")
            return None


# Global service instance
_analytics_service: AnalyticsService | None = None
_analytics_service_lock = threading.Lock()


def get_analytics_service(
    service: AnalyticsService | None = None,
    config_provider: ConfigProviderProtocol | None = None,
    model_registry: ModelRegistry | None = None,
) -> AnalyticsService:
    """Return a global analytics service instance.

    If ``service`` is provided, it becomes the global instance.  Otherwise an
    instance is created on first access.
    """
    global _analytics_service
    if service is not None:
        with _analytics_service_lock:
            _analytics_service = service
        return _analytics_service
    if _analytics_service is None:
        with _analytics_service_lock:
            if _analytics_service is None:
                _analytics_service = AnalyticsService(
                    config=config_provider,
                    model_registry=model_registry,
                    loader=create_loader(),
                    calculator=create_calculator(),
                    publisher=create_publisher(),
                    report_generator=SummaryReportGenerator(),
                )
    return _analytics_service


def create_analytics_service(
    config_provider: ConfigProviderProtocol | None = None,
    model_registry: ModelRegistry | None = None,
) -> AnalyticsService:
    """Create new analytics service instance"""
    return AnalyticsService(
        config=config_provider,
        model_registry=model_registry,
        loader=create_loader(),
        calculator=create_calculator(),
        publisher=create_publisher(),
        report_generator=SummaryReportGenerator(),
    )


__all__ = ["AnalyticsService", "get_analytics_service", "create_analytics_service"]
