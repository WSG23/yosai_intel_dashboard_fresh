#!/usr/bin/env python3
"""Analytics Service - Enhanced with Unique Patterns Analysis.

Uploaded files are validated with
``services.data_processing.unified_file_validator.UnifiedFileValidator`` before
processing to ensure they are present, non-empty and within the configured size
limits.
"""
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Tuple

import pandas as pd

from services.analytics.upload_analytics import UploadAnalyticsProcessor
from services.analytics_summary import generate_sample_analytics
from services.data_processing.processor import Processor
from advanced_cache import cache_with_lock
from core.security_validator import SecurityValidator
from services.db_analytics_helper import DatabaseAnalyticsHelper
from services.summary_reporting import SummaryReporter
from services.analytics.protocols import DataProcessorProtocol
from core.protocols import (
    AnalyticsServiceProtocol,
    ConfigurationProtocol,
    DatabaseProtocol,
    EventBusProtocol,
    StorageProtocol,
)


class ConfigProviderProtocol(Protocol):
    """Provide configuration values to services."""

    def get_database_config(self) -> Any:
        """Return the database configuration."""
        ...


class AnalyticsProviderProtocol(Protocol):
    """Basic analytics provider interface."""

    def process_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process ``df`` and return analytics metrics."""
        ...

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
    except Exception:
        pass


ensure_analytics_config()

logger = logging.getLogger(__name__)

from config.dynamic_config import dynamic_config

# Thresholds used for row count sanity checks
ROW_LIMIT_WARNING = 150
"""Warning threshold when exactly 150 rows are returned."""

LARGE_DATA_THRESHOLD = 1000
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
    ):
        self.database = database
        self.data_processor = data_processor or Processor(validator=SecurityValidator())
        self.config = config
        self.event_bus = event_bus
        self.storage = storage
        self.database_manager: Optional[Any] = None
        self._initialize_database()
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

        self.upload_processor = UploadAnalyticsProcessor(
            self.validation_service,
            self.processor,
        )
        self.db_helper = DatabaseAnalyticsHelper(self.database_manager)
        self.summary_reporter = SummaryReporter(self.database_manager)
        self.data_loader = self.processor

    def _initialize_database(self):
        """Initialize database connection"""
        try:
            if self.database is not None:
                self.database_manager = self.database
                self.db_helper = DatabaseAnalyticsHelper(self.database)
                self.summary_reporter = SummaryReporter(self.database)
                return

            from config.database_manager import DatabaseConfig as ManagerConfig
            from config.database_manager import DatabaseManager
            from config import get_database_config

            cfg = get_database_config()
            manager_cfg = ManagerConfig(
                type=cfg.type,
                host=cfg.host,
                port=cfg.port,
                name=cfg.name,
                user=cfg.user,
                password=cfg.password,
            )
            self.database_manager = DatabaseManager(manager_cfg)
            logger.info("Database manager initialized")
            self.db_helper = DatabaseAnalyticsHelper(self.database_manager)
            self.summary_reporter = SummaryReporter(self.database_manager)
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
            self.database_manager = None
            self.db_helper = DatabaseAnalyticsHelper(None)
            self.summary_reporter = SummaryReporter(None)

    def get_analytics_from_uploaded_data(self) -> Dict[str, Any]:
        """Get analytics from uploaded files using helper."""
        return self.upload_processor.get_analytics_from_uploaded_data()

    def get_analytics_by_source(self, source: str) -> Dict[str, Any]:
        """Get analytics from specified source with forced uploaded data check"""

        # FORCE CHECK: If uploaded data exists, use it regardless of source
        try:
            from services.upload_data_service import get_uploaded_data
            from services.interfaces import get_upload_data_service

            uploaded_data = get_uploaded_data(get_upload_data_service())

            if uploaded_data and source in ["uploaded", "sample"]:
                logger.info(f"Forcing uploaded data usage (source was: {source})")
                return self._process_uploaded_data_directly(uploaded_data)

        except Exception as e:
            logger.error(f"Uploaded data check failed: {e}")

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
        return self.upload_processor._process_uploaded_data_directly(uploaded_data)

    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Load uploaded data from the file upload page."""
        return self.upload_processor.load_uploaded_data()

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply standard column mappings and basic cleaning."""
        return self.upload_processor.clean_uploaded_dataframe(df)

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create a summary dictionary from a combined DataFrame."""
        return self.upload_processor.summarize_dataframe(df)

    def analyze_with_chunking(
        self, df: pd.DataFrame, analysis_types: List[str]
    ) -> Dict[str, Any]:
        """Analyze a DataFrame using chunked processing."""
        return self.upload_processor.analyze_with_chunking(df, analysis_types)

    def diagnose_data_flow(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Diagnostic method to check data processing flow."""
        return self.upload_processor.diagnose_data_flow(df)

    def _get_real_uploaded_data(self) -> Dict[str, Any]:
        """Load and summarize all uploaded records."""
        return self.upload_processor._get_real_uploaded_data()

    def _get_analytics_with_fixed_processor(self) -> Dict[str, Any]:
        """Get analytics using the sample file processor."""
        return self.upload_processor._get_analytics_with_fixed_processor()

    @cache_with_lock(ttl_seconds=600)
    def _get_database_analytics(self) -> Dict[str, Any]:
        """Get analytics from database."""
        return self.db_helper.get_analytics()

    @cache_with_lock(ttl_seconds=300)
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get a basic dashboard summary"""
        try:
            summary = self.get_analytics_from_uploaded_data()
            if self.event_bus:
                try:
                    self.event_bus.publish("analytics_update", summary)
                except Exception as exc:  # pragma: no cover - best effort
                    logger.debug("Event bus publish failed: %s", exc)
            return summary
        except Exception as e:
            logger.error(f"Dashboard summary failed: {e}")
            return {"status": "error", "message": str(e)}

    def _load_patterns_data(self, data_source: str | None) -> Tuple[pd.DataFrame, int]:
        """Load and clean data for unique patterns analysis."""
        logger = logging.getLogger(__name__)

        if data_source == "database":
            df, _meta = self.data_loader.get_processed_database()
            uploaded_data = {"database": df} if not df.empty else {}
        else:
            uploaded_data = self.load_uploaded_data()

        if not uploaded_data:
            return pd.DataFrame(), 0

        all_dfs: List[pd.DataFrame] = []
        total_original_rows = 0

        logger.info(f"📁 Found {len(uploaded_data)} uploaded files")

        for filename, df in uploaded_data.items():
            original_rows = len(df)
            total_original_rows += original_rows
            logger.info(f"   {filename}: {original_rows:,} rows")

            cleaned_df = self.clean_uploaded_dataframe(df)
            all_dfs.append(cleaned_df)
            logger.info(f"   After cleaning: {len(cleaned_df):,} rows")

        combined_df = (
            all_dfs[0] if len(all_dfs) == 1 else pd.concat(all_dfs, ignore_index=True)
        )

        return combined_df, total_original_rows

    def _verify_combined_data(self, df: pd.DataFrame, original_rows: int) -> None:
        """Log sanity checks for the combined dataframe."""
        logger = logging.getLogger(__name__)

        final_rows = len(df)
        logger.info(f"📊 COMBINED DATASET: {final_rows:,} total rows")

        if final_rows != original_rows:
            logger.warning(
                "⚠️  Data loss detected: %s → %s",
                f"{original_rows:,}",
                f"{final_rows:,}",
            )

        if final_rows == ROW_LIMIT_WARNING and original_rows > ROW_LIMIT_WARNING:
            logger.error("🚨 FOUND %s ROW LIMIT in unique patterns analysis!", ROW_LIMIT_WARNING)
            logger.error(f"   Original rows: {original_rows:,}")
            logger.error(f"   Final rows: {final_rows:,}")
        elif final_rows > LARGE_DATA_THRESHOLD:
            logger.info(f"✅ Processing large dataset: {final_rows:,} rows")

    def _calculate_pattern_stats(self, df: pd.DataFrame) -> Tuple[int, int, int, int]:
        """Calculate record, user, device and date span statistics."""
        logger = logging.getLogger(__name__)

        total_records = len(df)
        unique_users = (
            int(df["person_id"].nunique()) if "person_id" in df.columns else 0
        )
        unique_devices = int(df["door_id"].nunique()) if "door_id" in df.columns else 0

        date_span = 0
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            valid_dates = df["timestamp"].dropna()
            if len(valid_dates) > 0:
                date_span = (valid_dates.max() - valid_dates.min()).days

        logger.info("📈 STATISTICS:")
        logger.info(f"   Total records: {total_records:,}")
        logger.info(f"   Unique users: {unique_users:,}")
        logger.info(f"   Unique devices: {unique_devices:,}")
        if date_span:
            logger.info(f"   Date span: {date_span} days")

        return total_records, unique_users, unique_devices, date_span

    def _analyze_user_patterns(
        self, df: pd.DataFrame, unique_users: int
    ) -> Tuple[List[str], List[str], List[str]]:
        """Classify users by activity level."""
        logger = logging.getLogger(__name__)

        power_users: List[str] = []
        regular_users: List[str] = []
        occasional_users: List[str] = []

        if "person_id" in df.columns and unique_users > 0:
            user_stats = df.groupby("person_id").size()
            if len(user_stats) > 0:
                q80 = float(user_stats.quantile(0.8))
                q20 = float(user_stats.quantile(0.2))
                power_users = user_stats[user_stats.gt(q80)].index.tolist()
                regular_users = user_stats[user_stats.between(q20, q80)].index.tolist()
                occasional_users = user_stats[user_stats.lt(q20)].index.tolist()

        logger.info(f"   Power users: {len(power_users)}")
        logger.info(f"   Regular users: {len(regular_users)}")
        logger.info(f"   Occasional users: {len(occasional_users)}")

        return power_users, regular_users, occasional_users

    def _analyze_device_patterns(
        self, df: pd.DataFrame, unique_devices: int
    ) -> Tuple[List[str], List[str], List[str]]:
        """Classify devices by activity level."""
        logger = logging.getLogger(__name__)

        high_traffic: List[str] = []
        moderate_traffic: List[str] = []
        low_traffic: List[str] = []

        if "door_id" in df.columns and unique_devices > 0:
            device_stats = df.groupby("door_id").size()
            if len(device_stats) > 0:
                q80 = float(device_stats.quantile(0.8))
                q20 = float(device_stats.quantile(0.2))
                high_traffic = device_stats[device_stats.gt(q80)].index.tolist()
                moderate_traffic = device_stats[
                    device_stats.between(q20, q80)
                ].index.tolist()
                low_traffic = device_stats[device_stats.lt(q20)].index.tolist()

        logger.info(f"   High traffic devices: {len(high_traffic)}")
        logger.info(f"   Moderate traffic devices: {len(moderate_traffic)}")
        logger.info(f"   Low traffic devices: {len(low_traffic)}")

        return high_traffic, moderate_traffic, low_traffic

    def _count_interactions(self, df: pd.DataFrame) -> int:
        """Count unique user-device interactions."""
        if "person_id" in df.columns and "door_id" in df.columns:
            interaction_pairs = df.groupby(["person_id", "door_id"]).size()
            return len(interaction_pairs)
        return 0

    def _calculate_success_rate(self, df: pd.DataFrame) -> float:
        """Calculate overall access success rate."""
        if "access_result" in df.columns:
            success_mask = (
                df["access_result"]
                .str.lower()
                .str.contains("grant|allow|success|permit", case=False, na=False)
            )
            return success_mask.mean()
        return 0.0

    def _format_patterns_result(
        self,
        total_records: int,
        unique_users: int,
        unique_devices: int,
        date_span: int,
        power_users: List[str],
        regular_users: List[str],
        occasional_users: List[str],
        high_traffic: List[str],
        moderate_traffic: List[str],
        low_traffic: List[str],
        total_interactions: int,
        success_rate: float,
    ) -> Dict[str, Any]:
        """Build the final unique patterns analysis result."""
        return {
            "status": "success",
            "analysis_timestamp": datetime.now().isoformat(),
            "data_summary": {
                "total_records": total_records,
                "unique_entities": {
                    "users": unique_users,
                    "devices": unique_devices,
                    "interactions": total_interactions,
                },
                "date_range": {"span_days": date_span},
            },
            "user_patterns": {
                "total_unique_users": unique_users,
                "user_classifications": {
                    "power_users": power_users[:10],
                    "regular_users": regular_users[:10],
                    "occasional_users": occasional_users[:10],
                },
            },
            "device_patterns": {
                "total_unique_devices": unique_devices,
                "device_classifications": {
                    "high_traffic_devices": high_traffic[:10],
                    "moderate_traffic_devices": moderate_traffic[:10],
                    "low_traffic_devices": low_traffic[:10],
                    "secure_devices": [],
                    "popular_devices": high_traffic[:5],
                    "problematic_devices": [],
                },
            },
            "interaction_patterns": {
                "total_unique_interactions": total_interactions,
                "interaction_statistics": {"unique_pairs": total_interactions},
            },
            "temporal_patterns": {"date_span_days": date_span},
            "access_patterns": {
                "overall_success_rate": success_rate,
                "success_percentage": success_rate * 100,
            },
            "recommendations": [],
        }

    @cache_with_lock(ttl_seconds=600)
    def get_unique_patterns_analysis(self, data_source: str | None = None):
        """Get unique patterns analysis for the requested source."""
        logger = logging.getLogger(__name__)

        try:
            logger.info("🎯 Starting Unique Patterns Analysis")

            df, original_rows = self._load_patterns_data(data_source)
            if df.empty:
                logger.warning("❌ No uploaded data found for unique patterns analysis")
                return {
                    "status": "no_data",
                    "message": "No uploaded files available",
                    "data_summary": {"total_records": 0},
                }

            self._verify_combined_data(df, original_rows)

            (
                total_records,
                unique_users,
                unique_devices,
                date_span,
            ) = self._calculate_pattern_stats(df)

            power_users, regular_users, occasional_users = self._analyze_user_patterns(
                df, unique_users
            )
            (
                high_traffic_devices,
                moderate_traffic_devices,
                low_traffic_devices,
            ) = self._analyze_device_patterns(df, unique_devices)

            total_interactions = self._count_interactions(df)
            success_rate = self._calculate_success_rate(df)

            result = self._format_patterns_result(
                total_records,
                unique_users,
                unique_devices,
                date_span,
                power_users,
                regular_users,
                occasional_users,
                high_traffic_devices,
                moderate_traffic_devices,
                low_traffic_devices,
                total_interactions,
                success_rate,
            )

            result_total = result["data_summary"]["total_records"]
            logger.info("🎉 UNIQUE PATTERNS ANALYSIS COMPLETE")
            logger.info(f"   Result total_records: {result_total:,}")

            if result_total == ROW_LIMIT_WARNING and result_total != original_rows:
                logger.error(
                    "❌ STILL SHOWING %s - CHECK DATA PROCESSING!", ROW_LIMIT_WARNING
                )
            elif result_total == original_rows:
                logger.info(f"✅ SUCCESS: Correctly showing {result_total:,} rows")
            else:
                logger.warning(
                    "⚠️  Unexpected count: %s (expected %s)",
                    f"{result_total:,}",
                    f"{original_rows:,}",
                )

            if self.event_bus:
                try:
                    self.event_bus.publish("analytics_update", result)
                except Exception as exc:  # pragma: no cover - best effort
                    logger.debug("Event bus publish failed: %s", exc)

            return result

        except Exception as e:
            logger.error(f"❌ Unique patterns analysis failed: {e}")
            import traceback

            traceback.print_exc()

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
    def process_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Alias for :meth:`process_data` required by ``AnalyticsProviderProtocol``."""
        return self.process_data(df)

    def process_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process ``df`` and return a metrics dictionary."""
        cleaned = self.clean_uploaded_dataframe(df)
        return self.summarize_dataframe(cleaned)

    def get_metrics(self) -> Dict[str, Any]:
        """Return current analytics metrics."""
        return self.get_analytics_status()

    # ------------------------------------------------------------------
    # Placeholder implementations for abstract methods
    # ------------------------------------------------------------------
    def analyze_access_patterns(
        self, days: int, user_id: str | None = None
    ) -> Dict[str, Any]:
        """Analyze access patterns over the given timeframe."""
        logger.debug(
            "analyze_access_patterns called with days=%s user_id=%s",
            days,
            user_id,
        )
        return {"patterns": [], "days": days, "user_id": user_id}

    def detect_anomalies(
        self, data: pd.DataFrame, sensitivity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in the provided data."""
        logger.debug("detect_anomalies called with sensitivity=%s", sensitivity)
        return []

    def generate_report(self, report_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an analytics report."""
        logger.debug(
            "generate_report called with report_type=%s params=%s",
            report_type,
            params,
        )
        return {"report_type": report_type, "params": params}


# Global service instance
_analytics_service: Optional[AnalyticsService] = None
_analytics_service_lock = threading.Lock()


def get_analytics_service(
    service: Optional[AnalyticsService] = None,
    config_provider: ConfigProviderProtocol | None = None,
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
                _analytics_service = AnalyticsService(config=config_provider)
    return _analytics_service


def create_analytics_service(
    config_provider: ConfigProviderProtocol | None = None,
) -> AnalyticsService:
    """Create new analytics service instance"""
    return AnalyticsService(config=config_provider)


__all__ = ["AnalyticsService", "get_analytics_service", "create_analytics_service"]
