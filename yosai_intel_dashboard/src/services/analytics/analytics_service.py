from __future__ import annotations

import asyncio
import logging
import threading
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Protocol,
    Tuple,
    Union,
    cast,
)

from shared.events.names import EventName

from yosai_intel_dashboard.src.core.error_handling import (
    ErrorCategory,
    ErrorSeverity,
    with_error_handling,
)

try:
    from typing import override
except ImportError:  # pragma: no cover - for Python <3.12
    from typing_extensions import override

import pandas as pd
from pandas import DataFrame, Series
from pydantic import ValidationError

from validation.security_validator import SecurityValidator
from yosai_intel_dashboard.models.ml import ModelRegistry
from yosai_intel_dashboard.src.core.cache_manager import (
    CacheConfig,
    InMemoryCacheManager,
    cache_with_lock,
)
from yosai_intel_dashboard.src.core.di_decorators import inject, injectable
from yosai_intel_dashboard.src.core.interfaces import ConfigProviderProtocol
from yosai_intel_dashboard.src.core.interfaces.service_protocols import (
    AnalyticsDataLoaderProtocol,
    DatabaseAnalyticsRetrieverProtocol,
    get_analytics_data_loader,
    get_upload_data_service,
)
from yosai_intel_dashboard.src.services.analytics.calculator import Calculator
from yosai_intel_dashboard.src.services.analytics.orchestrator import (
    AnalyticsOrchestrator,
)
from yosai_intel_dashboard.src.services.analytics.protocols import (
    AnalyticsServiceProtocol,
    CalculatorProtocol,
    DataProcessorProtocol,
    PublishingProtocol,
    ReportGeneratorProtocol,
    UploadAnalyticsProtocol,
)
from yosai_intel_dashboard.src.services.publishing_service import PublishingService
from yosai_intel_dashboard.src.services.analytics_summary import (
    generate_sample_analytics,
)
from yosai_intel_dashboard.src.services.controllers.protocols import (
    UploadProcessingControllerProtocol,
)
from yosai_intel_dashboard.src.services.controllers.upload_controller import (
    UploadProcessingController,
)
from yosai_intel_dashboard.src.services.data_processing.processor import Processor
from yosai_intel_dashboard.src.services.helpers.database_initializer import (
    DatabaseInitializer,
)
from yosai_intel_dashboard.src.services.helpers.event_publisher import EventPublisher
from yosai_intel_dashboard.src.services.helpers.model_manager import ModelManager
from yosai_intel_dashboard.src.services.common.analytics_utils import (
    preload_active_models,
)
from yosai_intel_dashboard.src.services.protocols import UploadDataServiceProtocol
from yosai_intel_dashboard.src.services.summary_report_generator import (
    SummaryReportGenerator,
)
from yosai_intel_dashboard.src.services.upload_processing import (
    UploadAnalyticsProcessor,
)

from .schemas import AnalyticsQueryV1, AnalyticsSummaryV1
from .unicode import normalize_text

_cache_manager = InMemoryCacheManager(CacheConfig())


class AnalyticsProviderProtocol(Protocol):
    """Basic analytics provider interface."""

    def process_dataframe(self, df: DataFrame) -> Dict[str, Any]:
        """Process ``df`` and return analytics metrics."""
        ...

    def get_metrics(self) -> Dict[str, Any]:
        """Return current analytics metrics."""
        ...


# ----------------------------------------------------------------------
# Dependency protocol definitions
# ----------------------------------------------------------------------


class Database(Protocol):
    """Database dependency interface."""

    def execute_query(
        self, query: str, params: Optional[Tuple[Any, ...]] = None
    ) -> DataFrame:
        """Execute ``query`` and return a :class:`~pandas.DataFrame`."""

    def execute_command(
        self, command: str, params: Optional[Tuple[Any, ...]] = None
    ) -> None:
        """Execute a database command."""


class DataProcessor(DataProcessorProtocol, Protocol):
    """Data processor dependency interface."""


class Config(Protocol):
    """Configuration provider interface."""

    analytics: Any
    database: Any
    security: Any


class EventBus(Protocol):
    """Event bus dependency interface."""

    def publish(self, event: str, payload: Dict[str, Any]) -> None:
        """Publish ``payload`` under ``event`` name."""

from typing import Any, Dict

class AnalyticsService:
    """Minimal service returning placeholder analytics data."""

    def __init__(self) -> None:
        self._metrics: Dict[str, Any] = {}

    def get_analytics(self, source: str) -> Dict[str, Any]:
        """Return analytics data for ``source``."""
        uploaded_data = self.orchestrator.loader.load_uploaded_data()
        if uploaded_data and source in ["uploaded", "sample"]:
            logger.info(f"Forcing uploaded data usage (source was: {source})")
            return self.orchestrator.process_uploaded_data_directly(uploaded_data)

        if source == "sample":
            return generate_sample_analytics()
        if source == "uploaded":
            return {"status": "no_data", "message": "No uploaded files available"}
        if source == "database":
            return self.orchestrator.get_database_analytics()
        return {"status": "error", "message": f"Unknown source: {source}"}


@injectable
class AnalyticsService(AnalyticsServiceProtocol, AnalyticsProviderProtocol):
    """Analytics service implementing ``AnalyticsServiceProtocol``."""

    @inject
    def __init__(
        self,
        database: Database | None = None,
        data_processor: DataProcessor | None = None,
        config: Config | None = None,
        event_bus: EventBus | None = None,
        storage: Storage | None = None,
        upload_data_service: UploadDataServiceProtocol | None = None,
        model_registry: ModelRegistry | None = None,
        db_initializer: DatabaseInitializer | None = None,
        *,
        loader: AnalyticsDataLoaderProtocol | None = None,
        calculator: CalculatorProtocol | None = None,
        publisher: PublishingProtocol | None = None,
        report_generator: ReportGeneratorProtocol | None = None,
        db_retriever: DatabaseAnalyticsRetrieverProtocol | None = None,
        upload_controller: UploadProcessingControllerProtocol | None = None,
        upload_processor: UploadAnalyticsProtocol | None = None,
    ) -> None:
        self._inject_dependencies(
            database=database,
            data_processor=data_processor,
            config=config,
            event_bus=event_bus,
            storage=storage,
            upload_data_service=upload_data_service,
            model_registry=model_registry,
            db_initializer=db_initializer,
            upload_processor=upload_processor,
            upload_controller=upload_controller,
            report_generator=report_generator,
        )
        self._setup_database(db_retriever)
        self._create_orchestrator(loader, calculator, publisher)
        self.event_publisher = EventPublisher(self.publisher)
        self.router = DataSourceRouter(self.orchestrator)
        analytics_cfg = getattr(config, "analytics", None)
        model_dir = getattr(analytics_cfg, "ml_models_path", "models/ml")
        self.model_dir = Path(model_dir)
        self.models: Dict[str, Any] = {}

    def _inject_dependencies(
        self,
        *,
        database: Database | None,
        data_processor: DataProcessor | None,
        config: Config | None,
        event_bus: EventBus | None,
        storage: Storage | None,
        upload_data_service: UploadDataServiceProtocol | None,
        model_registry: ModelRegistry | None,
        db_initializer: DatabaseInitializer | None,
        upload_processor: UploadAnalyticsProtocol | None,
        upload_controller: UploadProcessingControllerProtocol | None,
        report_generator: ReportGeneratorProtocol | None,
    ) -> None:
        """Store injected dependencies and initialize helpers."""
        self.database = database
        if data_processor is None:
            raise ValueError("data_processor is required")
        self.data_processor = data_processor
        self.config = config
        self.event_bus = event_bus
        self.storage = storage
        self.upload_data_service = upload_data_service
        self.model_registry = model_registry
        self.model_manager = ModelManager(model_registry, config)
        self.validation_service = SecurityValidator()
        self.processor = data_processor
        self.data_loading_service = self.processor  # Legacy alias
        from yosai_intel_dashboard.src.services.data_processing.file_handler import (
            FileHandler,
        )

        self.file_handler = FileHandler()
        self.upload_processor = upload_processor
        self.upload_controller = upload_controller
        self.report_generator = report_generator
        self.db_initializer = db_initializer or DatabaseInitializer()
        self.database_manager: Any
        self.db_helper: Any
        self.summary_reporter: Any
        self.database_retriever: DatabaseAnalyticsRetrieverProtocol
        self.data_loader: AnalyticsDataLoaderProtocol
        self.calculator: CalculatorProtocol
        self.publisher: PublishingProtocol
        self.event_publisher: EventPublisher
        self.orchestrator: AnalyticsOrchestrator
        self.router: DataSourceRouter

    def _setup_database(
        self, db_retriever: DatabaseAnalyticsRetrieverProtocol | None
    ) -> None:
        """Configure database helpers via the initializer."""
        (
            self.database_manager,
            self.db_helper,
            self.summary_reporter,
            self.database_retriever,
        ) = self.db_initializer.setup(self.database, db_retriever)

    def _create_orchestrator(
        self,
        loader: AnalyticsDataLoaderProtocol | None,
        calculator: CalculatorProtocol | None,
        publisher: PublishingProtocol | None,
    ) -> None:
        """Build the orchestrator from loader, calculator and publisher."""
        if loader is None or calculator is None or publisher is None:
            raise ValueError("loader, calculator and publisher are required")
        self.data_loader = loader
        self.calculator = calculator
        self.publisher = publisher
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
        """Get analytics from the specified source."""
        try:
            query = AnalyticsQueryV1.model_validate({"source": source})
        except ValidationError:
            sanitized = normalize_text(source).strip().lower()
            logger.error(f"Invalid analytics source: {sanitized}")
            raise ValueError(f"Invalid analytics source: {sanitized}")

        normalized = normalize_text(query.source)
        result = self.router.get_analytics(normalized)
        summary = AnalyticsSummaryV1.model_validate(result)
        return summary.model_dump()

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
        df.columns = [normalize_text(c) for c in df.columns]
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

    def publish_event(
        self, payload: Dict[str, Any], event: str = EventName.ANALYTICS_UPDATE
    ) -> None:
        """Publish ``payload`` using the event publisher."""
        self.event_publisher.publish(payload, event)

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

    def _calculate_anomaly_score(self, values: Series) -> float:
        """Compute a basic anomaly score from numeric ``values``."""
        if values.empty:
            return 0.0
        return float(values.mean())

    def _get_template(self, name: str) -> Optional[Template]:
        """Retrieve a template named ``name`` from storage if available."""
        if self.storage is None:
            return None
        obj = self.storage.load(name)
        if isinstance(obj, (DataFrame, Series, bytes)):
            return None
        return cast(Template, obj)

    def _gather_report_data(self, df: DataFrame) -> Dict[str, Any]:
        """Collect summary and anomaly metrics for ``df``."""
        summary = self.summarize_dataframe(df)
        numeric = df.select_dtypes(include=["number"]).mean()
        anomaly = self._calculate_anomaly_score(numeric)
        return {"summary": summary, "anomaly_score": anomaly}

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
    def preload_active_models(self) -> None:
        """Load all active models from the registry into memory."""
        preload_active_models(self)

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
                _analytics_service = create_analytics_service(
                    config_provider=config_provider,
                    model_registry=model_registry,
                )
    return _analytics_service


def create_analytics_service(
    config_provider: ConfigProviderProtocol | None = None,
    model_registry: ModelRegistry | None = None,
) -> AnalyticsService:
    """Create new analytics service instance with default dependencies."""

    validation = SecurityValidator()
    processor = Processor(validator=validation)
    upload_service = get_upload_data_service()
    upload_processor = UploadAnalyticsProcessor(validation, processor)
    upload_controller = UploadProcessingController(
        validation,
        processor,
        upload_service,
        upload_processor,
    )
    loader = get_analytics_data_loader(upload_controller, processor)
    report_generator = SummaryReportGenerator()
    calculator = Calculator(report_generator)
    publisher = PublishingService()
    return AnalyticsService(
        data_processor=processor,
        config=config_provider,
        upload_data_service=upload_service,
        model_registry=model_registry,
        loader=loader,
        calculator=calculator,
        publisher=publisher,
        report_generator=report_generator,
        upload_controller=upload_controller,
        upload_processor=upload_processor,
    )


class RiskScoreResult(NamedTuple):
    """Simple risk score container."""

    score: float
    level: str


def _risk_level(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def calculate_risk_score(
    anomaly_component: float = 0.0,
    pattern_component: float = 0.0,
    behavior_component: float = 0.0,
) -> RiskScoreResult:
    """Combine numeric risk components into a final score."""

    score = (
        max(0.0, min(anomaly_component, 100.0))
        + max(0.0, min(pattern_component, 100.0))
        + max(0.0, min(behavior_component, 100.0))
    ) / 3
    score = round(score, 2)
    return RiskScoreResult(score=score, level=_risk_level(score))



def get_analytics_service() -> AnalyticsService:
    """Provide a default :class:`AnalyticsService` instance."""
    return AnalyticsService()
