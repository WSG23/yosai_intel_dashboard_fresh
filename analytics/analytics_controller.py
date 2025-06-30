"""
Analytics Controller Module
Consolidated controller for all analytics modules with unified callbacks
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import logging
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

# Import all analytics modules
from .security_patterns import SecurityPatternsAnalyzer, create_security_analyzer
from .access_trends import AccessTrendsAnalyzer, create_trends_analyzer
from .user_behavior import UserBehaviorAnalyzer, create_behavior_analyzer
from .anomaly_detection import AnomalyDetector, create_anomaly_detector
from .interactive_charts import SecurityChartsGenerator, create_charts_generator
from core.callback_manager import CallbackManager
from core.callback_events import CallbackEvent


@dataclass
class AnalyticsConfig:
    """Configuration for analytics processing"""

    enable_security_patterns: bool = True
    enable_access_trends: bool = True
    enable_user_behavior: bool = True
    enable_anomaly_detection: bool = True
    enable_interactive_charts: bool = True
    anomaly_sensitivity: float = 0.95
    parallel_processing: bool = True
    cache_results: bool = True
    cache_duration_minutes: int = 30


@dataclass
class AnalyticsResult:
    """Complete analytics result structure"""

    security_patterns: Dict[str, Any]
    access_trends: Dict[str, Any]
    user_behavior: Dict[str, Any]
    anomaly_detection: Dict[str, Any]
    interactive_charts: Dict[str, Any]
    processing_time: float
    data_summary: Dict[str, Any]
    generated_at: datetime
    status: str
    errors: List[str]


class AnalyticsController:
    """Unified controller for all analytics operations"""

    def __init__(
        self,
        config: Optional[AnalyticsConfig] = None,
        callback_manager: Optional[CallbackManager] = None,
    ):
        self.config = config or AnalyticsConfig()
        self.logger = logging.getLogger(__name__)

        # Initialize analyzers
        self.security_analyzer = (
            create_security_analyzer() if self.config.enable_security_patterns else None
        )
        self.trends_analyzer = (
            create_trends_analyzer() if self.config.enable_access_trends else None
        )
        self.behavior_analyzer = (
            create_behavior_analyzer() if self.config.enable_user_behavior else None
        )
        self.anomaly_detector = (
            create_anomaly_detector() if self.config.enable_anomaly_detection else None
        )
        self.charts_generator = (
            create_charts_generator() if self.config.enable_interactive_charts else None
        )

        # Cache for results
        self._cache = {}
        self._cache_timestamps = {}

        self._manager = callback_manager or CallbackManager()

        # Thread pool for parallel processing
        self._executor = (
            ThreadPoolExecutor(max_workers=5)
            if self.config.parallel_processing
            else None
        )

    _EVENT_MAP = {
        "on_analysis_start": CallbackEvent.ANALYSIS_START,
        "on_analysis_progress": CallbackEvent.ANALYSIS_PROGRESS,
        "on_analysis_complete": CallbackEvent.ANALYSIS_COMPLETE,
        "on_analysis_error": CallbackEvent.ANALYSIS_ERROR,
        "on_data_processed": CallbackEvent.DATA_PROCESSED,
    }

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register callback for specific events"""
        if event not in self._EVENT_MAP:
            raise ValueError(f"Unknown event type: {event}")
        self._manager.register_callback(self._EVENT_MAP[event], callback)

    def unregister_callback(self, event: str, callback: Callable) -> None:
        """Unregister callback for specific events"""
        # Simple removal by rebuilding list
        if event not in self._EVENT_MAP:
            return
        mapped = self._EVENT_MAP[event]
        self._manager.unregister_callback(mapped, callback)

    def _trigger_callbacks(self, event: str, *args, **kwargs) -> None:
        """Trigger all callbacks for an event"""
        if event not in self._EVENT_MAP:
            return
        self._manager.trigger(self._EVENT_MAP[event], *args, **kwargs)

    def analyze_all(
        self, df: pd.DataFrame, analysis_id: Optional[str] = None
    ) -> AnalyticsResult:
        """Run complete analytics analysis"""

        start_time = datetime.now()
        analysis_id = analysis_id or f"analysis_{int(start_time.timestamp())}"
        errors = []

        try:
            # Trigger start callbacks
            self._trigger_callbacks("on_analysis_start", analysis_id, df)

            # Check cache first
            if self.config.cache_results:
                cached_result = self._get_cached_result(df)
                if cached_result:
                    self.logger.info("Returning cached analytics result")
                    return cached_result

            # Validate and prepare data
            df_processed = self._prepare_data(df)
            data_summary = self._generate_data_summary(df_processed)

            self._trigger_callbacks("on_data_processed", analysis_id, data_summary)

            # Run analytics
            if self.config.parallel_processing and self._executor:
                results = self._run_parallel_analysis(df_processed, analysis_id)
            else:
                results = self._run_sequential_analysis(df_processed, analysis_id)

            # Create final result
            processing_time = (datetime.now() - start_time).total_seconds()

            analytics_result = AnalyticsResult(
                security_patterns=results.get("security_patterns", {}),
                access_trends=results.get("access_trends", {}),
                user_behavior=results.get("user_behavior", {}),
                anomaly_detection=results.get("anomaly_detection", {}),
                interactive_charts=results.get("interactive_charts", {}),
                processing_time=processing_time,
                data_summary=data_summary,
                generated_at=start_time,
                status="success",
                errors=errors,
            )

            # Cache result
            if self.config.cache_results:
                self._cache_result(df, analytics_result)

            # Trigger completion callbacks
            self._trigger_callbacks(
                "on_analysis_complete", analysis_id, analytics_result
            )

            return analytics_result

        except Exception as e:
            self.logger.error(f"Analytics analysis failed: {e}")
            errors.append(str(e))

            # Trigger error callbacks
            self._trigger_callbacks("on_analysis_error", analysis_id, e)

            # Return error result
            return AnalyticsResult(
                security_patterns={},
                access_trends={},
                user_behavior={},
                anomaly_detection={},
                interactive_charts={},
                processing_time=(datetime.now() - start_time).total_seconds(),
                data_summary=self._generate_data_summary(df),
                generated_at=start_time,
                status="error",
                errors=errors,
            )

    def analyze_specific(
        self,
        df: pd.DataFrame,
        analysis_types: List[str],
        analysis_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run specific analytics only"""

        start_time = datetime.now()
        analysis_id = analysis_id or f"specific_{int(start_time.timestamp())}"
        results = {}

        try:
            self._trigger_callbacks("on_analysis_start", analysis_id, df)

            df_processed = self._prepare_data(df)

            # Run only requested analytics
            for analysis_type in analysis_types:
                try:
                    self._trigger_callbacks(
                        "on_analysis_progress", analysis_id, analysis_type, 0
                    )

                    if analysis_type == "security_patterns" and self.security_analyzer:
                        results[analysis_type] = (
                            self.security_analyzer.analyze_patterns(df_processed)
                        )
                    elif analysis_type == "access_trends" and self.trends_analyzer:
                        results[analysis_type] = self.trends_analyzer.analyze_trends(
                            df_processed
                        )
                    elif analysis_type == "user_behavior" and self.behavior_analyzer:
                        results[analysis_type] = (
                            self.behavior_analyzer.analyze_behavior(df_processed)
                        )
                    elif analysis_type == "anomaly_detection" and self.anomaly_detector:
                        results[analysis_type] = self.anomaly_detector.detect_anomalies(
                            df_processed, self.config.anomaly_sensitivity
                        )
                    elif (
                        analysis_type == "interactive_charts" and self.charts_generator
                    ):
                        results[analysis_type] = (
                            self.charts_generator.generate_all_charts(df_processed)
                        )
                    else:
                        results[analysis_type] = {}

                    self._trigger_callbacks(
                        "on_analysis_progress", analysis_id, analysis_type, 100
                    )

                except Exception as e:
                    self.logger.error(f"Analysis {analysis_type} failed: {e}")
                    results[analysis_type] = {}

            self._trigger_callbacks("on_analysis_complete", analysis_id, results)
            return results

        except Exception as e:
            self.logger.error(f"Specific analysis failed: {e}")
            self._trigger_callbacks("on_analysis_error", analysis_id, e)
            return {}

    def _run_parallel_analysis(
        self, df: pd.DataFrame, analysis_id: str
    ) -> Dict[str, Any]:
        """Run analytics in parallel using thread pool"""

        futures = {}
        results = {}

        # Submit all enabled analytics to thread pool
        if self.security_analyzer:
            futures["security_patterns"] = self._executor.submit(
                self.security_analyzer.analyze_patterns, df
            )

        if self.trends_analyzer:
            futures["access_trends"] = self._executor.submit(
                self.trends_analyzer.analyze_trends, df
            )

        if self.behavior_analyzer:
            futures["user_behavior"] = self._executor.submit(
                self.behavior_analyzer.analyze_behavior, df
            )

        if self.anomaly_detector:
            futures["anomaly_detection"] = self._executor.submit(
                self.anomaly_detector.detect_anomalies,
                df,
                self.config.anomaly_sensitivity,
            )

        if self.charts_generator:
            futures["interactive_charts"] = self._executor.submit(
                self.charts_generator.generate_all_charts, df
            )

        # Collect results as they complete
        total_tasks = len(futures)
        completed_tasks = 0

        for analysis_type, future in futures.items():
            try:
                results[analysis_type] = future.result(timeout=300)  # 5 minute timeout
                completed_tasks += 1
                progress = (completed_tasks / total_tasks) * 100
                self._trigger_callbacks(
                    "on_analysis_progress", analysis_id, analysis_type, progress
                )

            except Exception as e:
                self.logger.error(f"Parallel analysis {analysis_type} failed: {e}")
                results[analysis_type] = {}

        return results

    def _run_sequential_analysis(
        self, df: pd.DataFrame, analysis_id: str
    ) -> Dict[str, Any]:
        """Run analytics sequentially"""

        results = {}
        analyses = []

        # Build list of enabled analyses
        if self.security_analyzer:
            analyses.append(
                ("security_patterns", self.security_analyzer.analyze_patterns)
            )
        if self.trends_analyzer:
            analyses.append(("access_trends", self.trends_analyzer.analyze_trends))
        if self.behavior_analyzer:
            analyses.append(("user_behavior", self.behavior_analyzer.analyze_behavior))
        if self.anomaly_detector:
            analyses.append(
                (
                    "anomaly_detection",
                    lambda df: self.anomaly_detector.detect_anomalies(
                        df, self.config.anomaly_sensitivity
                    ),
                )
            )
        if self.charts_generator:
            analyses.append(
                ("interactive_charts", self.charts_generator.generate_all_charts)
            )

        # Run each analysis sequentially
        total_analyses = len(analyses)
        for i, (analysis_type, analyzer_func) in enumerate(analyses):
            try:
                progress = (i / total_analyses) * 100
                self._trigger_callbacks(
                    "on_analysis_progress", analysis_id, analysis_type, progress
                )

                results[analysis_type] = analyzer_func(df)

                progress = ((i + 1) / total_analyses) * 100
                self._trigger_callbacks(
                    "on_analysis_progress", analysis_id, analysis_type, progress
                )

            except Exception as e:
                self.logger.error(f"Sequential analysis {analysis_type} failed: {e}")
                results[analysis_type] = {}

        return results

    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate data for analytics"""

        if df.empty:
            raise ValueError("DataFrame is empty")

        # Required columns check
        required_columns = [
            "event_id",
            "timestamp",
            "person_id",
            "door_id",
            "access_result",
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Data type conversions
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Sort by timestamp
        df = df.sort_values("timestamp").reset_index(drop=True)

        # Remove duplicates
        df = df.drop_duplicates(subset=["event_id"], keep="first")

        return df

    def _generate_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary of data for analytics"""

        if df.empty:
            return {
                "total_events": 0,
                "date_range": {"start": None, "end": None},
                "unique_users": 0,
                "unique_doors": 0,
                "data_quality": "empty",
            }

        return {
            "total_events": len(df),
            "date_range": {
                "start": (
                    df["timestamp"].min().isoformat()
                    if "timestamp" in df.columns
                    else None
                ),
                "end": (
                    df["timestamp"].max().isoformat()
                    if "timestamp" in df.columns
                    else None
                ),
            },
            "unique_users": df["person_id"].nunique(),
            "unique_doors": df["door_id"].nunique(),
            "access_success_rate": (
                (df["access_result"] == "Granted").mean() * 100
                if "access_result" in df.columns
                else 0
            ),
            "data_quality": self._assess_data_quality(df),
        }

    def _assess_data_quality(self, df: pd.DataFrame) -> str:
        """Assess quality of data"""

        if df.empty:
            return "empty"

        # Check for missing values in critical columns
        critical_columns = ["timestamp", "person_id", "door_id", "access_result"]
        missing_rates = []

        for col in critical_columns:
            if col in df.columns:
                missing_rate = df[col].isnull().mean()
                missing_rates.append(missing_rate)

        if not missing_rates:
            return "poor"

        avg_missing_rate = np.mean(missing_rates)

        if avg_missing_rate < 0.01:
            return "excellent"
        elif avg_missing_rate < 0.05:
            return "good"
        elif avg_missing_rate < 0.1:
            return "fair"
        else:
            return "poor"

    def _get_cache_key(self, df: pd.DataFrame) -> str:
        """Generate cache key for DataFrame"""

        # Create hash based on data shape and content sample
        data_hash = hash(
            (
                len(df),
                df.shape[1],
                df["timestamp"].min() if "timestamp" in df.columns else 0,
                df["timestamp"].max() if "timestamp" in df.columns else 0,
                df["person_id"].nunique() if "person_id" in df.columns else 0,
            )
        )

        return str(data_hash)

    def _get_cached_result(self, df: pd.DataFrame) -> Optional[AnalyticsResult]:
        """Get cached result if available and valid"""

        cache_key = self._get_cache_key(df)

        if cache_key in self._cache:
            cached_time = self._cache_timestamps.get(cache_key)
            if cached_time:
                age_minutes = (datetime.now() - cached_time).total_seconds() / 60
                if age_minutes < self.config.cache_duration_minutes:
                    return self._cache[cache_key]
                else:
                    # Cache expired, remove it
                    del self._cache[cache_key]
                    del self._cache_timestamps[cache_key]

        return None

    def _cache_result(self, df: pd.DataFrame, result: AnalyticsResult):
        """Cache analytics result"""

        cache_key = self._get_cache_key(df)
        self._cache[cache_key] = result
        self._cache_timestamps[cache_key] = datetime.now()

        # Limit cache size
        if len(self._cache) > 100:
            # Remove oldest entries
            oldest_keys = sorted(
                self._cache_timestamps.keys(), key=lambda k: self._cache_timestamps[k]
            )[:50]

            for key in oldest_keys:
                del self._cache[key]
                del self._cache_timestamps[key]

    def clear_cache(self):
        """Clear analytics cache"""
        self._cache.clear()
        self._cache_timestamps.clear()

    def get_analytics_status(self) -> Dict[str, Any]:
        """Get status of analytics modules"""

        return {
            "modules_enabled": {
                "security_patterns": self.config.enable_security_patterns,
                "access_trends": self.config.enable_access_trends,
                "user_behavior": self.config.enable_user_behavior,
                "anomaly_detection": self.config.enable_anomaly_detection,
                "interactive_charts": self.config.enable_interactive_charts,
            },
            "modules_loaded": {
                "security_patterns": self.security_analyzer is not None,
                "access_trends": self.trends_analyzer is not None,
                "user_behavior": self.behavior_analyzer is not None,
                "anomaly_detection": self.anomaly_detector is not None,
                "interactive_charts": self.charts_generator is not None,
            },
            "configuration": {
                "parallel_processing": self.config.parallel_processing,
                "cache_enabled": self.config.cache_results,
                "cache_duration_minutes": self.config.cache_duration_minutes,
                "anomaly_sensitivity": self.config.anomaly_sensitivity,
            },
            "cache_stats": {
                "cached_results": len(self._cache),
                "cache_memory_usage": sum(
                    len(str(result)) for result in self._cache.values()
                ),
            },
            "callback_counts": {
                event.name: len(self._manager.get_callbacks(event))
                for event in CallbackEvent
            },
        }

    def export_results(
        self, result: AnalyticsResult, export_format: str = "json"
    ) -> str:
        """Export analytics results in specified format"""

        if export_format.lower() == "json":
            return self._export_to_json(result)
        elif export_format.lower() == "summary":
            return self._export_to_summary(result)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")

    def _export_to_json(self, result: AnalyticsResult) -> str:
        """Export results to JSON format"""

        # Convert to serializable format
        export_data = {
            "metadata": {
                "generated_at": result.generated_at.isoformat(),
                "processing_time": result.processing_time,
                "status": result.status,
                "errors": result.errors,
            },
            "data_summary": result.data_summary,
            "security_patterns": result.security_patterns,
            "access_trends": result.access_trends,
            "user_behavior": result.user_behavior,
            "anomaly_detection": result.anomaly_detection,
            # Note: interactive_charts excluded due to Plotly figures not being JSON serializable
        }

        return json.dumps(export_data, indent=2, default=str)

    def _export_to_summary(self, result: AnalyticsResult) -> str:
        """Export results to human-readable summary"""

        summary_lines = [
            f"Analytics Report Generated: {result.generated_at}",
            f"Processing Time: {result.processing_time:.2f} seconds",
            f"Status: {result.status}",
            "",
            "=== DATA SUMMARY ===",
            f"Total Events: {result.data_summary.get('total_events', 0):,}",
            f"Unique Users: {result.data_summary.get('unique_users', 0)}",
            f"Unique Doors: {result.data_summary.get('unique_doors', 0)}",
            f"Success Rate: {result.data_summary.get('access_success_rate', 0):.1f}%",
            f"Data Quality: {result.data_summary.get('data_quality', 'unknown')}",
            "",
        ]

        # Add security patterns summary
        if result.security_patterns:
            score_obj = result.security_patterns.get("security_score", 0)
            score_val = getattr(score_obj, "score", score_obj)
            summary_lines.extend(
                [
                    "=== SECURITY PATTERNS ===",
                    f"Security Score: {score_val:.1f}/100",
                    f"Failed Access Events: {result.security_patterns.get('failed_access_patterns', {}).get('total', 0)}",
                    "",
                ]
            )

        # Add anomaly detection summary
        if result.anomaly_detection:
            anomaly_summary = result.anomaly_detection.get("anomaly_summary", {})
            summary_lines.extend(
                [
                    "=== ANOMALY DETECTION ===",
                    f"Total Anomalies: {anomaly_summary.get('total_anomalies', 0)}",
                    f"Risk Level: {result.anomaly_detection.get('risk_assessment', {}).get('risk_level', 'unknown')}",
                    "",
                ]
            )

        if result.errors:
            summary_lines.extend(["=== ERRORS ===", *result.errors, ""])

        return "\n".join(summary_lines)

    def __del__(self):
        """Cleanup resources"""
        if self._executor:
            self._executor.shutdown(wait=True)


# Convenience factory functions
def create_analytics_controller(
    config: Optional[AnalyticsConfig] = None,
) -> AnalyticsController:
    """Create analytics controller with default or custom configuration"""
    return AnalyticsController(config)


def create_default_controller() -> AnalyticsController:
    """Create analytics controller with default settings"""
    return AnalyticsController()


def create_performance_controller() -> AnalyticsController:
    """Create analytics controller optimized for performance"""
    config = AnalyticsConfig(
        parallel_processing=True, cache_results=True, cache_duration_minutes=60
    )
    return AnalyticsController(config)


def create_minimal_controller() -> AnalyticsController:
    """Create analytics controller with minimal features for testing"""
    config = AnalyticsConfig(
        enable_security_patterns=True,
        enable_access_trends=True,
        enable_user_behavior=False,
        enable_anomaly_detection=False,
        enable_interactive_charts=False,
        parallel_processing=False,
        cache_results=False,
    )
    return AnalyticsController(config)


# Export all classes and functions
__all__ = [
    "AnalyticsController",
    "AnalyticsConfig",
    "AnalyticsResult",
    "create_analytics_controller",
    "create_default_controller",
    "create_performance_controller",
    "create_minimal_controller",
]
