#!/usr/bin/env python3
"""
Analytics Service - Enhanced with Unique Patterns Analysis
"""
import pandas as pd
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from services.file_processing_service import FileProcessingService
from services.database_analytics_service import DatabaseAnalyticsService
from services.data_loader import DataLoader
from services.analytics_summary import (
    generate_basic_analytics,
    generate_sample_analytics,
    summarize_dataframe,
)
from services.data_validation import DataValidationService
from services.data_loading_service import DataLoadingService
from services.chunked_analysis import analyze_with_chunking
from services.result_formatting import regular_analysis

from utils.mapping_helpers import map_and_clean
from datetime import datetime, timedelta
import os

from analytics.db_interface import AnalyticsDataAccessor
from analytics.file_processing_utils import (
    stream_uploaded_file,
    update_counts,
    update_timestamp_range,
    aggregate_counts,
    calculate_date_range,
    build_result,
)


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


class AnalyticsService:
    """Complete analytics service that integrates all data sources"""

    def __init__(self):
        self.database_manager: Optional[Any] = None
        self._initialize_database()
        self.file_processing_service = FileProcessingService()
        self.validation_service = DataValidationService()
        self.data_loading_service = DataLoadingService(self.validation_service)
        self.database_analytics_service = DatabaseAnalyticsService(
            self.database_manager
        )
        self.data_loader = DataLoader()

    def _initialize_database(self):
        """Initialize database connection"""
        try:
            from config.database_manager import DatabaseManager
            from config.config import get_database_config

            db_config = get_database_config()
            self.database_manager = DatabaseManager(db_config)
            logger.info("Database manager initialized")
            self.database_analytics_service = DatabaseAnalyticsService(
                self.database_manager
            )
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
            self.database_manager = None

    def get_analytics_from_uploaded_data(self) -> Dict[str, Any]:
        """Get analytics from uploaded files using the file processor."""
        try:
            # Get uploaded file paths (not pre-processed data)
            from pages.file_upload import get_uploaded_filenames

            uploaded_files = get_uploaded_filenames()

            if not uploaded_files:
                return {"status": "no_data", "message": "No uploaded files available"}

            combined_df, processing_info, processed_files, total_records = (
                self.file_processing_service.process_files(uploaded_files)
            )

            if combined_df.empty:
                return {
                    "status": "error",
                    "message": "No files could be processed successfully",
                    "processing_info": processing_info,
                }

            # Generate analytics from the properly processed data
            analytics = generate_basic_analytics(combined_df)

            # Add processing information
            analytics.update(
                {
                    "data_source": "uploaded_files_fixed",
                    "total_files_processed": processed_files,
                    "total_files_attempted": len(uploaded_files),
                    "processing_info": processing_info,
                    "total_events": total_records,
                    "active_users": (
                        combined_df["person_id"].nunique()
                        if "person_id" in combined_df.columns
                        else 0
                    ),
                    "active_doors": (
                        combined_df["door_id"].nunique()
                        if "door_id" in combined_df.columns
                        else 0
                    ),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return analytics

        except Exception as e:
            logger.error(f"Error getting analytics from uploaded data: {e}")
            return {"status": "error", "message": str(e)}

    def get_analytics_by_source(self, source: str) -> Dict[str, Any]:
        """Get analytics from specified source with forced uploaded data check"""

        # FORCE CHECK: If uploaded data exists, use it regardless of source
        try:
            from pages.file_upload import get_uploaded_data

            uploaded_data = get_uploaded_data()

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
        try:
            from collections import Counter

            logger.info(f"Processing {len(uploaded_data)} uploaded files directly...")

            processing_info: Dict[str, Any] = {}
            total_events = 0
            user_counts: Counter[str] = Counter()
            door_counts: Counter[str] = Counter()
            min_ts: Optional[pd.Timestamp] = None
            max_ts: Optional[pd.Timestamp] = None

            for filename, source in uploaded_data.items():
                try:
                    chunks = stream_uploaded_file(self.data_loading_service, source)
                    file_events, min_ts, max_ts = aggregate_counts(
                        chunks, user_counts, door_counts, min_ts, max_ts
                    )
                    processing_info[filename] = {"rows": file_events, "status": "ok"}
                    total_events += file_events
                except Exception as e:  # pragma: no cover - best effort
                    processing_info[filename] = {"rows": 0, "status": f"error: {e}"}
                    logger.error(f"Error processing {filename}: {e}")

            if not processing_info:
                return {"status": "error", "message": "No uploaded files processed"}

            date_range = calculate_date_range(min_ts, max_ts)

            result = build_result(
                total_events, user_counts, door_counts, date_range, processing_info
            )

            return result

        except Exception as e:  # pragma: no cover - unexpected
            logger.error(f"Direct processing failed: {e}")
            return {"status": "error", "message": str(e)}


    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Load uploaded data from the file upload page."""
        try:
            from pages.file_upload import get_uploaded_data

            return get_uploaded_data() or {}
        except Exception as e:  # pragma: no cover - best effort
            logger.error(f"Error loading uploaded data: {e}")
            return {}

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply standard column mappings and basic cleaning."""
        return map_and_clean(df)

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create a summary dictionary from a combined DataFrame."""
        return summarize_dataframe(df)

    def analyze_with_chunking(
        self, df: pd.DataFrame, analysis_types: List[str]
    ) -> Dict[str, Any]:
        """Analyze a DataFrame using chunked processing."""
        return analyze_with_chunking(df, self.validation_service, analysis_types)

    def diagnose_data_flow(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Diagnostic method to check data processing flow."""
        logger.info("=== Data Flow Diagnosis ===")
        logger.info(f"Input DataFrame: {len(df)} rows, {len(df.columns)} columns")
        logger.info(
            f"Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:,.1f} MB"
        )

        validator = self.validation_service

        logger.info(
            f"Validator config: upload_mb={validator.max_upload_mb}, analysis_mb={validator.max_analysis_mb}, chunk_size={validator.chunk_size}"
        )

        cleaned_df, needs_chunking = validator.validate_for_analysis(df.copy())
        logger.info(
            f"After validation: {len(cleaned_df)} rows, needs_chunking={needs_chunking}"
        )

        if needs_chunking:
            chunk_size = validator.get_optimal_chunk_size(cleaned_df)
            logger.info(f"Optimal chunk size: {chunk_size}")

        return {
            "input_rows": len(df),
            "validated_rows": len(cleaned_df),
            "needs_chunking": needs_chunking,
            "validator_config": {
                "max_upload_mb": validator.max_upload_mb,
                "max_analysis_mb": validator.max_analysis_mb,
                "chunk_size": validator.chunk_size,
            },
        }


    def _get_real_uploaded_data(self) -> Dict[str, Any]:
        """Load and summarize all uploaded records."""
        try:
            uploaded_data = self.load_uploaded_data()
            if not uploaded_data:
                return {"status": "no_data", "message": "No uploaded files available"}

            logger.info(f"Processing {len(uploaded_data)} uploaded files...")

            all_dfs = []
            total_original_rows = 0

            for filename, df in uploaded_data.items():
                logger.info(f"Processing {filename}: {len(df):,} rows")
                cleaned = self.clean_uploaded_dataframe(df)
                all_dfs.append(cleaned)
                total_original_rows += len(df)

            combined_df = pd.concat(all_dfs, ignore_index=True)

            logger.info(f"Combined: {len(combined_df):,} total rows")

            summary = self.summarize_dataframe(combined_df)
            summary.update(
                {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "files_processed": len(uploaded_data),
                    "original_total_rows": total_original_rows,
                }
            )

            logger.info("Analytics result:")
            logger.info(f"Total Events: {summary['total_events']:,}")
            logger.info(f"Active Users: {summary['active_users']:,}")
            logger.info(f"Active Doors: {summary['active_doors']:,}")

            return summary

        except Exception as e:
            logger.error(f"Error processing uploaded data: {e}")
            return {
                "status": "error",
                "message": f"Error processing uploaded data: {str(e)}",
                "total_events": 0,
            }

    def _get_analytics_with_fixed_processor(self) -> Dict[str, Any]:
        """Get analytics using the sample file processor."""

        from config.config import get_sample_files_config

        sample_cfg = get_sample_files_config()
        csv_file = os.getenv("SAMPLE_CSV_PATH", sample_cfg.csv_path)
        json_file = os.getenv("SAMPLE_JSON_PATH", sample_cfg.json_path)

        try:
            from services import FileProcessor
            import pandas as pd
            import json

            processor = FileProcessor(
                upload_folder="temp", allowed_extensions={"csv", "json", "xlsx"}
            )
            all_data = []

            # Process CSV file
            if os.path.exists(csv_file):
                df_csv = pd.read_csv(csv_file)
                result = processor._validate_data(df_csv)
                if result["valid"]:
                    processed_df = result["data"]
                    processed_df["source_file"] = "csv"
                    all_data.append(processed_df)

            # Process JSON file
            if os.path.exists(json_file):
                with open(json_file, "r", encoding="utf-8", errors="replace") as f:
                    json_data = json.load(f)
                df_json = pd.DataFrame(json_data)
                result = processor._validate_data(df_json)
                if result["valid"]:
                    processed_df = result["data"]
                    processed_df["source_file"] = "json"
                    all_data.append(processed_df)

            if all_data:
                combined_df = pd.concat(all_data, ignore_index=True)

                return {
                    "status": "success",
                    "total_events": len(combined_df),
                    "active_users": combined_df["person_id"].nunique(),
                    "active_doors": combined_df["door_id"].nunique(),
                    "data_source": "fixed_processor",
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error in fixed processor analytics: {e}")
            return {"status": "error", "message": str(e)}

        return {"status": "no_data", "message": "Files not available"}

    def _get_database_analytics(self) -> Dict[str, Any]:
        """Get analytics from database"""
        if not self.database_analytics_service:
            return {"status": "error", "message": "Database not available"}

        return self.database_analytics_service.get_analytics()

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get a basic dashboard summary"""
        try:
            summary = self.get_analytics_from_uploaded_data()
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
            logger.warning(f"⚠️  Data loss detected: {original_rows:,} → {final_rows:,}")

        if final_rows == 150 and original_rows > 150:
            logger.error("🚨 FOUND 150 ROW LIMIT in unique patterns analysis!")
            logger.error(f"   Original rows: {original_rows:,}")
            logger.error(f"   Final rows: {final_rows:,}")
        elif final_rows > 1000:
            logger.info(f"✅ Processing large dataset: {final_rows:,} rows")

    def _calculate_pattern_stats(self, df: pd.DataFrame) -> Tuple[int, int, int, int]:
        """Calculate record, user, device and date span statistics."""
        logger = logging.getLogger(__name__)

        total_records = len(df)
        unique_users = df["person_id"].nunique() if "person_id" in df.columns else 0
        unique_devices = df["door_id"].nunique() if "door_id" in df.columns else 0

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
                q80 = user_stats.quantile(0.8)
                q20 = user_stats.quantile(0.2)
                power_users = user_stats[user_stats > q80].index.tolist()
                regular_users = user_stats[user_stats.between(q20, q80)].index.tolist()
                occasional_users = user_stats[user_stats < q20].index.tolist()

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
                q80 = device_stats.quantile(0.8)
                q20 = device_stats.quantile(0.2)
                high_traffic = device_stats[device_stats > q80].index.tolist()
                moderate_traffic = device_stats[
                    device_stats.between(q20, q80)
                ].index.tolist()
                low_traffic = device_stats[device_stats < q20].index.tolist()

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

    def get_unique_patterns_analysis(self, data_source: str | None = None):
        """Get unique patterns analysis for the requested source."""
        import logging

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

            if result_total == 150 and result_total != original_rows:
                logger.error("❌ STILL SHOWING 150 - CHECK DATA PROCESSING!")
            elif result_total == original_rows:
                logger.info(f"✅ SUCCESS: Correctly showing {result_total:,} rows")
            else:
                logger.warning(
                    f"⚠️  Unexpected count: {result_total:,} (expected {original_rows:,})"
                )

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
        health = {"service": "healthy", "timestamp": datetime.now().isoformat()}

        # Check database
        if self.database_manager:
            try:
                health["database"] = (
                    "healthy" if self.database_manager.health_check() else "unhealthy"
                )
            except:
                health["database"] = "unhealthy"
        else:
            health["database"] = "not_configured"

        # Check file upload
        try:
            from pages.file_upload import get_uploaded_filenames

            health["uploaded_files"] = len(get_uploaded_filenames())
        except ImportError:
            health["uploaded_files"] = "not_available"

        return health

    def get_data_source_options(self) -> List[Dict[str, str]]:
        """Get available data source options"""
        options = [{"label": "Sample Data", "value": "sample"}]

        # Check for uploaded data
        try:
            from pages.file_upload import get_uploaded_filenames

            uploaded_files = get_uploaded_filenames()
            if uploaded_files:
                options.append(
                    {
                        "label": f"Uploaded Files ({len(uploaded_files)})",
                        "value": "uploaded",
                    }
                )
        except ImportError:
            pass

        # Check for database
        if self.database_manager and self.database_manager.health_check():
            options.append({"label": "Database", "value": "database"})

        return options

    def get_date_range_options(self) -> Dict[str, str]:
        """Get default date range options"""
        from datetime import datetime, timedelta

        return {
            "start": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "end": datetime.now().strftime("%Y-%m-%d"),
        }

    def get_analytics_status(self) -> Dict[str, Any]:
        """Get current analytics status"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "data_sources_available": len(self.get_data_source_options()),
            "service_health": self.health_check(),
        }

        try:
            from pages.file_upload import get_uploaded_filenames

            status["uploaded_files"] = len(get_uploaded_filenames())
        except ImportError:
            status["uploaded_files"] = 0

        return status


# Global service instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service(
    service: Optional[AnalyticsService] = None,
) -> AnalyticsService:
    """Return a global analytics service instance.

    If ``service`` is provided, it becomes the global instance.  Otherwise an
    instance is created on first access.
    """
    global _analytics_service
    if service is not None:
        _analytics_service = service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service


def create_analytics_service() -> AnalyticsService:
    """Create new analytics service instance"""
    return AnalyticsService()


__all__ = ["AnalyticsService", "get_analytics_service", "create_analytics_service"]
