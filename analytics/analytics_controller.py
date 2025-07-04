"""
Enhanced Analytics Controller
Replace the entire content of analytics/analytics_controller.py with this code
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from callback_controller import CallbackController, CallbackEvent
from security.unicode_security_handler import UnicodeSecurityHandler

# Import enhanced analyzers
from .security_patterns import SecurityPatternsAnalyzer, create_security_analyzer
from .access_trends import AccessTrendsAnalyzer, create_trends_analyzer
from .user_behavior import UserBehaviorAnalyzer, create_behavior_analyzer
from .anomaly_detection import AnomalyDetector, create_anomaly_detector


# Consolidated Callback System - using global controller


# Unicode Handler
class UnicodeHandler:
    """Robust Unicode handling for problematic characters"""

    @staticmethod
    def clean_unicode_string(text: str) -> str:
        """Clean string of problematic Unicode characters"""
        if not isinstance(text, str):
            text = str(text)

        return UnicodeSecurityHandler.sanitize_unicode_input(text)

    @staticmethod
    def clean_dataframe_unicode(df: pd.DataFrame) -> pd.DataFrame:
        """Clean all string columns in DataFrame"""
        df_clean = df.copy()

        string_columns = df_clean.select_dtypes(include=["object"]).columns
        for col in string_columns:
            df_clean[col] = df_clean[col].apply(UnicodeSecurityHandler.sanitize_unicode_input)

        return df_clean


@dataclass
class AnalyticsConfig:
    """Configuration for analytics processing"""

    enable_security_patterns: bool = True
    enable_access_trends: bool = True
    enable_user_behavior: bool = True
    enable_anomaly_detection: bool = True
    enable_interactive_charts: bool = False
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
    """Enhanced analytics controller with consolidated callbacks"""

    def __init__(
        self,
        config: Optional[AnalyticsConfig] = None,
        controller: Optional[CallbackController] = None,
    ):
        self.config = config or AnalyticsConfig()
        self.controller = controller or CallbackController()
        self.logger = logging.getLogger(__name__)

        # Initialize enhanced analyzers
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

        # Thread pool for parallel processing
        if self.config.parallel_processing:
            self._executor = ThreadPoolExecutor(max_workers=4)
        else:
            self._executor = None

    def analyze(
        self, df: pd.DataFrame, analysis_id: Optional[str] = None
    ) -> AnalyticsResult:
        """Run complete enhanced analytics with consolidated callbacks"""
        start_time = datetime.now()
        analysis_id = analysis_id or f"enhanced_{int(start_time.timestamp())}"

        try:
            # Clean Unicode issues
            df_clean = UnicodeHandler.clean_dataframe_unicode(df)

            # Trigger start callback
            self.controller.fire_event(
                CallbackEvent.ANALYSIS_START,
                analysis_id,
                {"total_records": len(df_clean), "start_time": start_time.isoformat()},
            )

            # Run enhanced analytics
            results = {}
            errors = []

            if self.security_analyzer:
                try:
                    security_result = self.security_analyzer.analyze_patterns(df_clean)
                    results["security_patterns"] = security_result

                    # Trigger threat detection callbacks if needed
                    if isinstance(security_result, dict):
                        risk_level = security_result.get("risk_level", "low")
                        if risk_level in ["critical", "high"]:
                            self.controller.fire_event(
                                CallbackEvent.SECURITY_THREAT_DETECTED,
                                analysis_id,
                                {
                                    "risk_level": risk_level,
                                    "score": security_result.get("security_score", 0),
                                },
                            )

                except Exception as e:
                    self.logger.error(f"Security analysis failed: {e}")
                    results["security_patterns"] = {}
                    errors.append(f"Security analysis: {str(e)}")

            if self.trends_analyzer:
                try:
                    trends_result = self.trends_analyzer.analyze_trends(df_clean)
                    results["access_trends"] = trends_result

                    # Trigger trend change callbacks if needed
                    if isinstance(trends_result, dict):
                        trend = trends_result.get("overall_trend", "stable")
                        if trend == "decreasing":
                            strength = trends_result.get("trend_strength", 0)
                            if strength > 0.7:
                                self.controller.fire_event(
                                    CallbackEvent.TREND_CHANGE_DETECTED,
                                    analysis_id,
                                    {"trend": trend, "strength": strength},
                                )

                except Exception as e:
                    self.logger.error(f"Trends analysis failed: {e}")
                    results["access_trends"] = {}
                    errors.append(f"Trends analysis: {str(e)}")

            if self.behavior_analyzer:
                try:
                    behavior_result = self.behavior_analyzer.analyze_behavior(df_clean)
                    results["user_behavior"] = behavior_result

                    # Trigger behavior risk callbacks if needed
                    if isinstance(behavior_result, dict):
                        high_risk_count = behavior_result.get("high_risk_users", 0)
                        if high_risk_count > 0:
                            self.controller.fire_event(
                                CallbackEvent.BEHAVIOR_RISK_IDENTIFIED,
                                analysis_id,
                                {"high_risk_count": high_risk_count},
                            )

                except Exception as e:
                    self.logger.error(f"Behavior analysis failed: {e}")
                    results["user_behavior"] = {}
                    errors.append(f"Behavior analysis: {str(e)}")

            if self.anomaly_detector:
                try:
                    anomaly_result = self.anomaly_detector.detect_anomalies(
                        df_clean, self.config.anomaly_sensitivity
                    )
                    results["anomaly_detection"] = anomaly_result

                    # Trigger anomaly detection callbacks if needed
                    if isinstance(anomaly_result, dict):
                        total_anomalies = anomaly_result.get("anomalies_detected", 0)
                        threat_level = anomaly_result.get("threat_level", "low")
                        if total_anomalies > 0 and threat_level in ["critical", "high"]:
                            self.controller.fire_event(
                                CallbackEvent.ANOMALY_DETECTED,
                                analysis_id,
                                {
                                    "total_anomalies": total_anomalies,
                                    "threat_level": threat_level,
                                },
                            )

                except Exception as e:
                    self.logger.error(f"Anomaly analysis failed: {e}")
                    results["anomaly_detection"] = {}
                    errors.append(f"Anomaly analysis: {str(e)}")

            # Charts placeholder
            results["interactive_charts"] = {}

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            # Generate data summary
            data_summary = self._generate_data_summary(df_clean)

            # Trigger completion callback
            self.controller.fire_event(
                CallbackEvent.ANALYSIS_COMPLETE,
                analysis_id,
                {
                    "processing_time": processing_time,
                    "modules_completed": list(results.keys()),
                    "total_records_processed": len(df_clean),
                },
            )

            return AnalyticsResult(
                security_patterns=results.get("security_patterns", {}),
                access_trends=results.get("access_trends", {}),
                user_behavior=results.get("user_behavior", {}),
                anomaly_detection=results.get("anomaly_detection", {}),
                interactive_charts=results.get("interactive_charts", {}),
                processing_time=processing_time,
                data_summary=data_summary,
                generated_at=start_time,
                status="success" if not errors else "partial_success",
                errors=errors,
            )

        except Exception as e:
            self.logger.error(f"Enhanced analytics failed: {e}")

            # Trigger error callback
            self.controller.fire_event(
                CallbackEvent.ANALYSIS_ERROR,
                analysis_id,
                {"error": str(e), "error_type": type(e).__name__},
            )

            return AnalyticsResult(
                security_patterns={},
                access_trends={},
                user_behavior={},
                anomaly_detection={},
                interactive_charts={},
                processing_time=(datetime.now() - start_time).total_seconds(),
                data_summary={},
                generated_at=start_time,
                status="error",
                errors=[str(e)],
            )

    def _generate_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary of the input data"""
        try:
            return {
                "total_records": len(df),
                "unique_users": (
                    int(df["person_id"].nunique())
                    if "person_id" in df.columns
                    else 0
                ),
                "unique_doors": (
                    int(df["door_id"].nunique())
                    if "door_id" in df.columns
                    else 0
                ),
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
                "success_rate": (
                    (df["access_result"] == "Granted").mean()
                    if "access_result" in df.columns
                    else 0
                ),
            }
        except Exception as e:
            self.logger.warning(f"Data summary generation failed: {e}")
            return {"total_records": len(df)}

    def register_callback(self, event: CallbackEvent, callback):
        """Register callback with the controller"""
        self.controller.register_callback(event, callback)

    def unregister_callback(self, event: CallbackEvent, callback):
        """Unregister callback from the controller"""
        self.controller.unregister_callback(event, callback)

    # Legacy compatibility methods
    def analyze_specific(
        self,
        df: pd.DataFrame,
        analysis_types: List[str],
        analysis_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run specific analytics only - legacy compatibility"""

        # Map legacy analysis types to new system
        type_mapping = {
            "security_patterns": "security_patterns",
            "access_trends": "access_trends",
            "user_behavior": "user_behavior",
            "anomaly_detection": "anomaly_detection",
        }

        # Temporarily disable modules not requested
        original_config = {
            "enable_security_patterns": self.config.enable_security_patterns,
            "enable_access_trends": self.config.enable_access_trends,
            "enable_user_behavior": self.config.enable_user_behavior,
            "enable_anomaly_detection": self.config.enable_anomaly_detection,
        }

        # Disable all, then enable only requested
        self.config.enable_security_patterns = "security_patterns" in analysis_types
        self.config.enable_access_trends = "access_trends" in analysis_types
        self.config.enable_user_behavior = "user_behavior" in analysis_types
        self.config.enable_anomaly_detection = "anomaly_detection" in analysis_types

        try:
            # Run analysis
            result = self.analyze(df, analysis_id)

            # Extract only requested results
            filtered_results = {}
            for analysis_type in analysis_types:
                if analysis_type in type_mapping:
                    mapped_type = type_mapping[analysis_type]
                    filtered_results[mapped_type] = getattr(result, mapped_type, {})

            return filtered_results

        finally:
            # Restore original configuration
            self.config.enable_security_patterns = original_config[
                "enable_security_patterns"
            ]
            self.config.enable_access_trends = original_config["enable_access_trends"]
            self.config.enable_user_behavior = original_config["enable_user_behavior"]
            self.config.enable_anomaly_detection = original_config[
                "enable_anomaly_detection"
            ]

    def _trigger_callbacks(self, event_name: str, analysis_id: str, *args):
        """Legacy callback trigger method for backward compatibility"""

        # Map legacy event names to new events
        event_mapping = {
            "on_analysis_start": CallbackEvent.ANALYSIS_START,
            "on_analysis_progress": CallbackEvent.ANALYSIS_PROGRESS,
            "on_analysis_complete": CallbackEvent.ANALYSIS_COMPLETE,
            "on_analysis_error": CallbackEvent.ANALYSIS_ERROR,
        }

        if event_name in event_mapping:
            event = event_mapping[event_name]
            data = {"legacy_args": args} if args else {}
            self.controller.fire_event(event, analysis_id, data)


# Export classes for compatibility
__all__ = [
    "AnalyticsController",
    "AnalyticsConfig",
    "AnalyticsResult",
    "CallbackController",
    "CallbackEvent",
    "UnicodeHandler",
]
