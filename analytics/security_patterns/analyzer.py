"""Security Patterns Analyzer.

This module applies machine learning techniques to identify suspicious
access behavior. It combines statistical anomaly detection, pattern
analysis and risk scoring to generate a comprehensive security assessment
with actionable recommendations.
"""

import logging
import warnings
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from database.baseline_metrics import BaselineMetricsDB
from utils.sklearn_compat import optional_import

from .chunk_processor import ChunkedDataProcessor, MemoryConfig

IsolationForest = optional_import("sklearn.ensemble.IsolationForest")
DataConversionWarning = optional_import("sklearn.exceptions.DataConversionWarning")
StandardScaler = optional_import("sklearn.preprocessing.StandardScaler")

if IsolationForest is None:  # pragma: no cover - fallback definitions

    class IsolationForest:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError("scikit-learn is required for IsolationForest")


if DataConversionWarning is None:  # pragma: no cover

    class DataConversionWarning(RuntimeWarning):
        pass


if StandardScaler is None:  # pragma: no cover

    class StandardScaler:  # type: ignore
        def fit_transform(self, X):
            return X

        def transform(self, X):
            return X


from analytics_core.callbacks.unified_callback_manager import (
    CallbackManager as SecurityCallbackController,
)
from security_callback_controller import (
    SecurityEvent,
    emit_security_event,
    security_callback_controller,
)

from ..security_metrics import SecurityMetrics
from ..security_score_calculator import SecurityScoreCalculator
from .access_no_exit_detection import detect_access_no_exit
from .badge_clone_detection import detect_badge_clone
from .clearance_violation_detection import detect_clearance_violations
from .composite_score import detect_composite_score
from .config import SecurityPatternsConfig
from .critical_door_detection import detect_critical_door_anomalies
from .data_prep import prepare_security_data
from .forced_entry_detection import detect_forced_entry
from .multiple_attempts_detection import detect_multiple_attempts
from .odd_area_detection import detect_odd_area
from .odd_area_time_detection import detect_odd_area_time
from .odd_door_detection import detect_odd_door_usage
from .odd_path_detection import detect_odd_path
from .odd_time_detection import detect_odd_time
from .pattern_detection import detect_pattern_threats

from .pattern_drift_detection import detect_pattern_drift
from .statistical_detection import detect_statistical_threats
from .tailgate_detection import detect_tailgate
from .types import ThreatIndicator
from .unaccompanied_visitor_detection import detect_unaccompanied_visitors

# Ignore warnings from scikit-learn about missing feature names and automatic
# data type conversions. These arise during DataFrame-based model training and
# are safe to suppress.
warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names",
    category=UserWarning,
    module="sklearn",
)
warnings.filterwarnings(
    "ignore",
    category=DataConversionWarning,
    module="sklearn",
)


@dataclass
class SecurityAssessment:
    """Comprehensive security assessment result"""

    overall_score: float  # 0-100
    risk_level: str
    confidence_interval: Tuple[float, float]
    threat_indicators: List[ThreatIndicator]
    pattern_analysis: Dict[str, Any]
    recommendations: List[str]


@dataclass
class BehaviorProfile:
    """Baseline behavior profile for a user or door."""

    entity_type: str
    entity_id: str
    after_hours_rate: float
    failure_rate: float
    total_events: int


class SecurityPatternsAnalyzer:
    """Enhanced security patterns analyzer with ML-based threat detection"""

    def __init__(
        self,
        contamination: float = 0.1,
        confidence_threshold: float = 0.7,
        logger: Optional[logging.Logger] = None,
        config: Optional[SecurityPatternsConfig] = None,
    ):
        self.contamination = contamination
        self.confidence_threshold = confidence_threshold
        self.logger = logger or logging.getLogger(__name__)
        self.unified_callbacks = security_callback_controller
        self.config = config or SecurityPatternsConfig()
        self.baseline_db = BaselineMetricsDB()

        # Initialize ML models
        self.isolation_forest = IsolationForest(
            contamination=contamination, random_state=42, n_estimators=100
        )
        self.scaler = StandardScaler()
        self.chunk_processor = ChunkedDataProcessor(
            MemoryConfig(max_memory_mb=500, chunk_size=50_000),
            logger=self.logger,
        )

    def analyze_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Main analysis method with legacy compatibility"""
        try:
            result = self.analyze_security_patterns(df)
            return self._convert_to_legacy_format(result)
        except Exception as e:
            self.logger.error(f"Security analysis failed: {e}")
            return self._empty_legacy_result()

    def analyze_security_patterns(self, df: pd.DataFrame) -> SecurityAssessment:
        """Enhanced security analysis method"""
        try:
            df_clean = self._prepare_security_data(df)

            # Update stored behavior baselines
            self._update_behavior_profiles(df_clean)

            threat_indicators = self._collect_threat_indicators(df_clean)

            security_score = self._calculate_comprehensive_score(
                df_clean, threat_indicators
            )

            pattern_analysis = self.safe_analyze_patterns(df_clean)
            recommendations = self._generate_security_recommendations(
                threat_indicators, pattern_analysis
            )

            risk_level = self._determine_risk_level(security_score, threat_indicators)
            confidence_interval = self._calculate_confidence_interval(
                df_clean, security_score
            )

            self._trigger_threat_callbacks(threat_indicators)
            self._trigger_analysis_complete(security_score, risk_level)

            return SecurityAssessment(
                overall_score=security_score,
                risk_level=risk_level,
                confidence_interval=confidence_interval,
                threat_indicators=threat_indicators,
                pattern_analysis=pattern_analysis,
                recommendations=recommendations,
            )

        except Exception as e:
            self.logger.error(f"Security analysis failed: {e}")
            return self._empty_security_assessment()

    def _collect_threat_indicators(self, df: pd.DataFrame) -> List[ThreatIndicator]:
        """Run all threat detection methods and return a combined list."""
        threat_indicators: List[ThreatIndicator] = []

        threat_indicators.extend(self._detect_statistical_threats(df))
        threat_indicators.extend(self._detect_pattern_threats(df))
        threat_indicators.extend(detect_critical_door_anomalies(df, self.logger))
        threat_indicators.extend(detect_tailgate(df, self.logger))
        threat_indicators.extend(
            detect_badge_clone(
                df,
                logger=self.logger,
                travel_time_limit=self.config.travel_time_limit,
            )
        )
        threat_indicators.extend(detect_odd_door_usage(df, self.logger))
        threat_indicators.extend(detect_odd_time(df, self.logger))
        threat_indicators.extend(detect_odd_path(df, self.logger))
        threat_indicators.extend(detect_odd_area(df, self.logger))
        threat_indicators.extend(detect_odd_area_time(df, self.logger))
        threat_indicators.extend(
            detect_multiple_attempts(
                df,
                logger=self.logger,
                window=self.config.attempts_window,
                threshold=self.config.attempts_threshold,
            )
        )
        threat_indicators.extend(detect_forced_entry(df, self.logger))
        threat_indicators.extend(
            detect_access_no_exit(
                df,
                logger=self.logger,
                timeout=self.config.no_exit_timeout,
            )
        )

        threat_indicators.extend(detect_pattern_drift(df, self.logger))
        threat_indicators.extend(detect_clearance_violations(df, self.logger))
        threat_indicators.extend(
            detect_unaccompanied_visitors(
                df,
                logger=self.logger,
                window=self.config.visitor_window,
            )
        )
        threat_indicators.extend(detect_composite_score(df, self.logger))

        return threat_indicators

    def _trigger_threat_callbacks(self, threats: List[ThreatIndicator]) -> None:
        """Emit events for any critical threats detected."""
        for threat in threats:
            if threat.severity == "critical":
                self.unified_callbacks.trigger(
                    SecurityEvent.THREAT_DETECTED,
                    {
                        "threat_type": threat.threat_type,
                        "description": threat.description,
                        "confidence": threat.confidence,
                        "attack": threat.attack,
                    },
                )
                self._emit_anomaly_detected(threat)

    def _trigger_analysis_complete(self, score: float, risk_level: str) -> None:
        """Emit events signalling completion of an analysis run."""
        self.unified_callbacks.trigger(
            SecurityEvent.ANALYSIS_COMPLETE,
            {"score": score, "risk_level": risk_level},
        )
        self._emit_score_calculated(score, risk_level)

    def _prepare_security_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and clean data for security analysis"""
        return prepare_security_data(df, self.logger)

    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Alias for backward compatibility."""
        try:
            return self._prepare_security_data(df)
        except Exception as e:
            self.logger.warning(f"Data preparation failed: {e}")
            raise

    def _update_behavior_profiles(self, df: pd.DataFrame) -> None:
        """Create or update baseline behavior profiles for users and doors."""
        for user_id, group in df.groupby("person_id"):
            metrics = {
                "after_hours_rate": float(group["is_after_hours"].mean()),
                "failure_rate": float(1 - group["access_granted"].mean()),
                "total_events": len(group),
            }
            try:
                self.baseline_db.update_baseline("user", str(user_id), metrics)
            except Exception as exc:  # pragma: no cover - log and continue
                self.logger.warning(
                    "Failed to update user baseline %s: %s", user_id, exc
                )

        for door_id, group in df.groupby("door_id"):
            metrics = {
                "after_hours_rate": float(group["is_after_hours"].mean()),
                "failure_rate": float(1 - group["access_granted"].mean()),
                "total_events": len(group),
            }
            try:
                self.baseline_db.update_baseline("door", str(door_id), metrics)
            except Exception as exc:  # pragma: no cover - log and continue
                self.logger.warning(
                    "Failed to update door baseline %s: %s", door_id, exc
                )

    def _detect_statistical_threats(self, df: pd.DataFrame) -> List[ThreatIndicator]:
        """Detect threats using statistical methods"""
        return detect_statistical_threats(df, self.logger)

    def _detect_failure_rate_anomalies(self, df: pd.DataFrame) -> List[ThreatIndicator]:
        """Detect unusual failure rate patterns"""
        threats = detect_failure_rate_anomalies(df, self.logger)
        try:
            for user_id, group in df.groupby("person_id"):
                current_rate = float(1 - group["access_granted"].mean())
                baseline = self.baseline_db.get_baseline("user", str(user_id)).get(
                    "failure_rate"
                )
                if (
                    baseline is not None
                    and current_rate > baseline * 1.5
                    and current_rate - baseline > 0.1
                ):
                    threats.append(
                        ThreatIndicator(
                            threat_type="failure_rate_deviation",
                            severity=(
                                "high" if current_rate - baseline > 0.3 else "medium"
                            ),
                            confidence=min(0.99, current_rate - baseline),
                            description=(
                                f"User {user_id} failure rate {current_rate:.2%} exceeds baseline {baseline:.2%}"
                            ),
                            evidence={
                                "user_id": str(user_id),
                                "current_rate": current_rate,
                                "baseline_rate": baseline,
                            },
                            timestamp=pd.Timestamp.utcnow(),
                            affected_entities=[str(user_id)],
                        )
                    )
        except Exception as exc:  # pragma: no cover - log and continue
            self.logger.warning("Baseline failure rate check failed: %s", exc)

        return threats

    def _detect_frequency_anomalies(self, df: pd.DataFrame) -> List[ThreatIndicator]:
        """Detect unusual access frequency patterns"""
        threats = detect_frequency_anomalies(df, self.logger)
        try:
            event_counts = df["person_id"].value_counts()
            for user_id, count in event_counts.items():
                baseline = self.baseline_db.get_baseline("user", str(user_id)).get(
                    "total_events"
                )
                if (
                    baseline is not None
                    and count > baseline * 2
                    and count - baseline > 10
                ):
                    threats.append(
                        ThreatIndicator(
                            threat_type="access_frequency_deviation",
                            severity="medium" if count < baseline * 3 else "high",
                            confidence=min(0.99, (count - baseline) / max(baseline, 1)),
                            description=(
                                f"User {user_id} access count {count} exceeds baseline {baseline}"
                            ),
                            evidence={
                                "user_id": str(user_id),
                                "current_count": int(count),
                                "baseline_count": baseline,
                            },
                            timestamp=pd.Timestamp.utcnow(),
                            affected_entities=[str(user_id)],
                        )
                    )
        except Exception as exc:  # pragma: no cover - log and continue
            self.logger.warning("Baseline frequency check failed: %s", exc)

        return threats

    def _detect_pattern_threats(self, df: pd.DataFrame) -> List[ThreatIndicator]:
        """Detect pattern-based security threats"""
        return detect_pattern_threats(df, self.logger)

    def _detect_rapid_attempts(self, df: pd.DataFrame) -> List[ThreatIndicator]:
        """Detect rapid successive access attempts"""
        from .pattern_detection import detect_rapid_attempts

        return detect_rapid_attempts(df, self.logger)

    def _detect_after_hours_anomalies(self, df: pd.DataFrame) -> List[ThreatIndicator]:
        """Detect suspicious after-hours access patterns"""
        from .pattern_detection import detect_after_hours_anomalies

        threats = detect_after_hours_anomalies(df, self.logger)

        try:
            after_hours = df[df["is_after_hours"] == True]
            user_counts = after_hours["person_id"].value_counts()
            for user_id, count in user_counts.items():
                total = len(df[df["person_id"] == user_id])
                rate = count / total if total else 0
                baseline = self.baseline_db.get_baseline("user", str(user_id)).get(
                    "after_hours_rate"
                )
                if (
                    baseline is not None
                    and rate > baseline * 1.5
                    and rate - baseline > 0.1
                ):
                    threats.append(
                        ThreatIndicator(
                            threat_type="after_hours_deviation",
                            severity="medium" if rate - baseline < 0.3 else "high",
                            confidence=min(0.99, rate - baseline),
                            description=(
                                f"User {user_id} after-hours rate {rate:.2%} exceeds baseline {baseline:.2%}"
                            ),
                            evidence={
                                "user_id": str(user_id),
                                "current_rate": rate,
                                "baseline_rate": baseline,
                            },
                            timestamp=pd.Timestamp.utcnow(),
                            affected_entities=[str(user_id)],
                        )
                    )

            # Door-level deviations
            door_counts = after_hours["door_id"].value_counts()
            for door_id, count in door_counts.items():
                total = len(df[df["door_id"] == door_id])
                rate = count / total if total else 0
                baseline = self.baseline_db.get_baseline("door", str(door_id)).get(
                    "after_hours_rate"
                )
                if (
                    baseline is not None
                    and rate > baseline * 1.5
                    and rate - baseline > 0.1
                ):
                    threats.append(
                        ThreatIndicator(
                            threat_type="door_after_hours_deviation",
                            severity="medium" if rate - baseline < 0.3 else "high",
                            confidence=min(0.99, rate - baseline),
                            description=(
                                f"Door {door_id} after-hours rate {rate:.2%} exceeds baseline {baseline:.2%}"
                            ),
                            evidence={
                                "door_id": str(door_id),
                                "current_rate": rate,
                                "baseline_rate": baseline,
                            },
                            timestamp=pd.Timestamp.utcnow(),
                            affected_entities=[str(door_id)],
                        )
                    )
        except Exception as exc:  # pragma: no cover - log and continue
            self.logger.warning("Baseline after-hours check failed: %s", exc)

        return threats

    def _detect_critical_door_risks(self, df: pd.DataFrame) -> List[ThreatIndicator]:
        """Detect high risk attempts on critical doors"""
        from .pattern_detection import detect_critical_door_risks

        return detect_critical_door_risks(df, self.logger)

    def _calculate_comprehensive_score(
        self, df: pd.DataFrame, threats: List[ThreatIndicator]
    ) -> float:
        """Calculate comprehensive security score (0-100)"""
        base_score = 100.0

        # Penalty for each threat based on severity and confidence
        severity_weights = {"critical": 25, "high": 15, "medium": 8, "low": 3}

        total_penalty = 0
        for threat in threats:
            penalty = severity_weights.get(threat.severity, 3) * threat.confidence
            total_penalty += penalty

        # Additional penalties for overall statistics
        failure_rate = 1 - df["access_granted"].mean()
        failure_penalty = min(30, failure_rate * 100)

        after_hours_rate = df["is_after_hours"].mean()
        after_hours_penalty = min(10, after_hours_rate * 50)

        total_penalty += failure_penalty + after_hours_penalty

        final_score = max(0, base_score - total_penalty)
        return round(final_score, 2)

    def _analyze_access_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall access patterns for security assessment"""
        patterns = {
            "temporal_distribution": {},
            "user_distribution": {},
            "failure_patterns": {},
        }

        try:
            # Temporal patterns
            hourly_dist = df["hour"].value_counts().sort_index()
            patterns["temporal_distribution"] = {
                "peak_hours": hourly_dist.nlargest(3).index.tolist(),
                "after_hours_percentage": df["is_after_hours"].mean() * 100,
                "weekend_percentage": df["is_weekend"].mean() * 100,
            }

            # User patterns
            user_activity = df.groupby("person_id").agg(
                {"event_id": "count", "access_granted": "mean"}
            )

            patterns["user_distribution"] = {
                "total_users": len(user_activity),
                "average_events_per_user": user_activity["event_id"].mean(),
                "average_success_rate": user_activity["access_granted"].mean(),
            }

            # Failure patterns
            failed_attempts = df[df["access_granted"] == 0]
            if len(failed_attempts) > 0:
                patterns["failure_patterns"] = {
                    "total_failures": len(failed_attempts),
                    "failure_rate": len(failed_attempts) / len(df),
                    "top_failure_users": failed_attempts["person_id"]
                    .value_counts()
                    .head(5)
                    .to_dict(),
                }

        except Exception as e:
            self.logger.warning(f"Pattern analysis failed: {e}")

        return patterns

    def _generate_security_recommendations(
        self, threats: List[ThreatIndicator], patterns: Dict[str, Any]
    ) -> List[str]:
        """Generate security recommendations"""
        recommendations = []

        critical_threats = [t for t in threats if t.severity == "critical"]
        high_threats = [t for t in threats if t.severity == "high"]

        if critical_threats:
            recommendations.append(
                f"URGENT: {len(critical_threats)} critical security threats detected. "
                "Immediate investigation required."
            )

        if high_threats:
            recommendations.append(
                f"HIGH PRIORITY: {len(high_threats)} high-severity threats require attention."
            )

        failure_patterns = patterns.get("failure_patterns", {})
        if failure_patterns.get("failure_rate", 0) > 0.1:
            recommendations.append(
                "High failure rate detected (>10%). Review access control systems."
            )

        # Threat type specific recommendations
        threat_types = [t.threat_type for t in threats]
        if "rapid_access_attempts" in threat_types:
            recommendations.append(
                "Rapid access attempts detected. Consider implementing rate limiting."
            )

        if "excessive_after_hours_access" in threat_types:
            recommendations.append(
                "Excessive after-hours activity detected. Review after-hours policies."
            )

        if not recommendations:
            recommendations.append(
                "No significant security issues detected. Continue monitoring."
            )

        return recommendations

    def _determine_risk_level(
        self, score: float, threats: List[ThreatIndicator]
    ) -> str:
        """Determine overall risk level"""
        critical_threats = len([t for t in threats if t.severity == "critical"])
        high_threats = len([t for t in threats if t.severity == "high"])

        if score < 30 or critical_threats >= 3:
            return "critical"
        elif score < 50 or critical_threats >= 1 or high_threats >= 3:
            return "high"
        elif score < 70 or high_threats >= 1:
            return "medium"
        else:
            return "low"

    def _calculate_confidence_interval(
        self, df: pd.DataFrame, score: float
    ) -> Tuple[float, float]:
        """Calculate confidence interval for security score"""
        n_samples = len(df)
        if n_samples < 30:
            return (max(0, score - 20), min(100, score + 20))

        failure_rate = 1 - df["access_granted"].mean()
        std_error = np.sqrt(failure_rate * (1 - failure_rate) / n_samples)

        margin_of_error = 1.96 * std_error * 100

        lower_bound = max(0, score - margin_of_error)
        upper_bound = min(100, score + margin_of_error)

        return (round(lower_bound, 2), round(upper_bound, 2))

    def _analyze_failed_access(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze failed access attempts and summarize statistics."""
        summary = {
            "total": 0,
            "failure_rate": 0.0,
            "high_risk_users": {},
            "peak_failure_times": [],
            "top_failure_doors": {},
            "patterns": {},
            "risk_level": "low",
        }

        try:
            failed = df[df.get("access_granted", 1) == 0]
            summary["total"] = int(len(failed))
            if len(df) > 0:
                summary["failure_rate"] = round(len(failed) / len(df), 4)

            if not failed.empty:
                summary["high_risk_users"] = (
                    failed["person_id"].value_counts().head(5).to_dict()
                )
                if "hour" in failed.columns:
                    summary["peak_failure_times"] = (
                        failed["hour"].value_counts().nlargest(3).index.tolist()
                    )
                if "door_id" in failed.columns:
                    summary["top_failure_doors"] = (
                        failed["door_id"].value_counts().head(3).to_dict()
                    )

                summary["patterns"] = {
                    "after_hours_rate": float(
                        failed.get("is_after_hours", pd.Series([])).mean()
                    ),
                    "weekend_rate": float(
                        failed.get("is_weekend", pd.Series([])).mean()
                    ),
                }

                rate = summary["failure_rate"]
                if rate >= 0.5 or len(summary["high_risk_users"]) > 3:
                    summary["risk_level"] = "high"
                elif rate >= 0.2:
                    summary["risk_level"] = "medium"
        except Exception as e:
            self.logger.warning(f"Failed access analysis failed: {e}")

        return summary

    def _calculate_enterprise_security_score(self, df: pd.DataFrame) -> SecurityMetrics:
        """Calculate enterprise security score using the calculator."""
        try:
            calculator = SecurityScoreCalculator()
            result = calculator.calculate_security_score_fixed(df)
            return SecurityMetrics(
                score=float(result.get("score", 0.0)),
                threat_level=result.get("threat_level", "unknown"),
                confidence_interval=tuple(
                    result.get("confidence_interval", (0.0, 0.0))
                ),
                method=result.get("method", "unknown"),
            )
        except Exception as e:
            self.logger.warning(f"Enterprise security score calculation failed: {e}")
            return SecurityMetrics(0.0, "unknown", (0.0, 0.0), "none")

    def _calculate_security_score(self, df: pd.DataFrame) -> SecurityMetrics:
        """Compatibility wrapper for enterprise security scoring."""
        return self._calculate_enterprise_security_score(df)

    def _emit_anomaly_detected(self, threat: ThreatIndicator) -> None:
        """Emit an anomaly detected event."""
        emit_security_event(
            SecurityEvent.ANOMALY_DETECTED,
            {
                "threat_type": threat.threat_type,
                "severity": threat.severity,
                "confidence": threat.confidence,
                "attack": threat.attack,
            },
        )

    def _emit_score_calculated(self, score: float, risk_level: str) -> None:
        """Emit event when a security score has been calculated."""
        emit_security_event(
            SecurityEvent.SCORE_CALCULATED,
            {"score": score, "risk_level": risk_level},
        )

    def _convert_to_legacy_format(self, result: SecurityAssessment) -> Dict[str, Any]:
        """Convert SecurityAssessment to legacy dictionary format"""
        return {
            "security_score": result.overall_score,
            "risk_level": result.risk_level,
            "confidence_interval": result.confidence_interval,
            "threat_count": len(result.threat_indicators),
            "critical_threats": len(
                [t for t in result.threat_indicators if t.severity == "critical"]
            ),
            "recommendations": result.recommendations,
            "pattern_analysis": result.pattern_analysis,
            "threats": [
                {
                    "type": t.threat_type,
                    "severity": t.severity,
                    "confidence": t.confidence,
                    "description": t.description,
                    "affected_entities": t.affected_entities,
                    "attack": t.attack,
                }
                for t in result.threat_indicators
            ],
            # Legacy compatibility fields
            "failed_attempts": len(
                [t for t in result.threat_indicators if "failure" in t.threat_type]
            ),
            "score": result.overall_score,
        }

    def _empty_security_assessment(self) -> SecurityAssessment:
        """Return empty security assessment for error cases"""
        return SecurityAssessment(
            overall_score=0.0,
            risk_level="unknown",
            confidence_interval=(0.0, 0.0),
            threat_indicators=[],
            pattern_analysis={},
            recommendations=["Unable to perform security analysis due to data issues"],
        )

    def _empty_legacy_result(self) -> Dict[str, Any]:
        """Return empty result in legacy format"""
        return {
            "security_score": 0.0,
            "risk_level": "unknown",
            "confidence_interval": (0.0, 0.0),
            "threat_count": 0,
            "critical_threats": 0,
            "recommendations": [
                "Unable to perform security analysis due to data issues"
            ],
            "pattern_analysis": {},
            "threats": [],
            "failed_attempts": 0,
            "score": 0.0,
        }


class PaginatedAnalyzer(SecurityPatternsAnalyzer):
    """Chunk-aware analyzer that limits memory usage."""

    def __init__(
        self,
        *,
        chunk_size: int = 50000,
        max_memory_mb: int = 500,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.chunk_size = chunk_size
        self.max_memory_mb = max_memory_mb

    def _iter_chunks(self, df: pd.DataFrame) -> Iterable[pd.DataFrame]:
        for i in range(0, len(df), self.chunk_size):
            yield df.iloc[i : i + self.chunk_size]

    def analyze_patterns_chunked(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze security patterns using chunked processing."""
        est_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        if est_mb <= self.max_memory_mb:
            return self.analyze_patterns(df)

        total_events = 0
        success_sum = 0
        after_hours_sum = 0
        weekend_sum = 0
        hourly_counts: Dict[int, int] = defaultdict(int)
        user_event_count: Dict[Any, int] = defaultdict(int)
        user_success_sum: Dict[Any, int] = defaultdict(int)
        failure_count = 0
        failure_users: Dict[Any, int] = defaultdict(int)
        threats: List[ThreatIndicator] = []

        for chunk in self._iter_chunks(df):
            prepared = self._prepare_security_data(chunk)
            total_events += len(prepared)
            success_sum += int(prepared["access_granted"].sum())
            after_hours_sum += int(prepared["is_after_hours"].sum())
            weekend_sum += int(prepared["is_weekend"].sum())
            for hour, cnt in prepared["hour"].value_counts().items():
                hourly_counts[int(hour)] += int(cnt)

            group = prepared.groupby("person_id").agg(
                event_count=("event_id", "count"),
                success_sum=("access_granted", "sum"),
            )
            for pid, row in group.iterrows():
                user_event_count[pid] += int(row["event_count"])
                user_success_sum[pid] += int(row["success_sum"])

            failures = prepared[prepared["access_granted"] == 0]
            failure_count += len(failures)
            for pid, cnt in failures["person_id"].value_counts().items():
                failure_users[pid] += int(cnt)

            threats.extend(self._detect_statistical_threats(prepared))
            threats.extend(self._detect_pattern_threats(prepared))

        patterns = self._compile_patterns(
            total_events,
            after_hours_sum,
            weekend_sum,
            hourly_counts,
            user_event_count,
            user_success_sum,
            failure_count,
            failure_users,
        )

        security_score = self._calculate_score_from_counts(
            total_events, success_sum, after_hours_sum, threats
        )
        recommendations = self._generate_security_recommendations(threats, patterns)
        risk_level = self._determine_risk_level(security_score, threats)
        confidence_interval = self._confidence_from_counts(
            total_events, success_sum, security_score
        )

        self._trigger_threat_callbacks(threats)
        self._trigger_analysis_complete(security_score, risk_level)

        result = SecurityAssessment(
            overall_score=security_score,
            risk_level=risk_level,
            confidence_interval=confidence_interval,
            threat_indicators=threats,
            pattern_analysis=patterns,
            recommendations=recommendations,
        )
        return self._convert_to_legacy_format(result)

    def _compile_patterns(
        self,
        total_events: int,
        after_hours_sum: int,
        weekend_sum: int,
        hourly_counts: Dict[int, int],
        user_event_count: Dict[Any, int],
        user_success_sum: Dict[Any, int],
        failure_count: int,
        failure_users: Dict[Any, int],
    ) -> Dict[str, Any]:
        patterns = {
            "temporal_distribution": {},
            "user_distribution": {},
            "failure_patterns": {},
        }

        if total_events:
            series = pd.Series(hourly_counts).sort_index()
            patterns["temporal_distribution"] = {
                "peak_hours": series.nlargest(3).index.tolist(),
                "after_hours_percentage": (after_hours_sum / total_events) * 100,
                "weekend_percentage": (weekend_sum / total_events) * 100,
            }

            total_users = len(user_event_count)
            total_events_all = sum(user_event_count.values())
            avg_events = total_events_all / total_users if total_users else 0
            avg_success = (
                sum(user_success_sum.values()) / total_events_all
                if total_events_all
                else 0
            )
            patterns["user_distribution"] = {
                "total_users": total_users,
                "average_events_per_user": avg_events,
                "average_success_rate": avg_success,
            }

            if failure_count:
                top = sorted(failure_users.items(), key=lambda x: x[1], reverse=True)[
                    :5
                ]
                patterns["failure_patterns"] = {
                    "total_failures": failure_count,
                    "failure_rate": failure_count / total_events,
                    "top_failure_users": {u: c for u, c in top},
                }

        return patterns

    def _calculate_score_from_counts(
        self,
        total_events: int,
        success_sum: int,
        after_hours_sum: int,
        threats: List[ThreatIndicator],
    ) -> float:
        severity_weights = {"critical": 25, "high": 15, "medium": 8, "low": 3}
        total_penalty = sum(
            severity_weights.get(t.severity, 3) * t.confidence for t in threats
        )

        if total_events == 0:
            return 0.0

        failure_rate = 1 - (success_sum / total_events)
        after_hours_rate = after_hours_sum / total_events
        total_penalty += min(30, failure_rate * 100)
        total_penalty += min(10, after_hours_rate * 50)
        return round(max(0, 100.0 - total_penalty), 2)

    def _confidence_from_counts(
        self, total_events: int, success_sum: int, score: float
    ) -> Tuple[float, float]:
        if total_events < 30:
            return (max(0, score - 20), min(100, score + 20))

        failure_rate = 1 - (success_sum / total_events)
        std_error = np.sqrt(failure_rate * (1 - failure_rate) / total_events)
        margin = 1.96 * std_error * 100
        lower = max(0, score - margin)
        upper = min(100, score + margin)
        return (round(lower, 2), round(upper, 2))

    # ------------------------------------------------------------------
    def safe_analyze_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Memory-safe access pattern analysis."""

        counts = {
            "total_events": 0,
            "after_hours_sum": 0,
            "weekend_sum": 0,
            "hourly_counts": defaultdict(int),
            "user_event_count": defaultdict(int),
            "user_success_sum": defaultdict(int),
            "failure_count": 0,
            "failure_users": defaultdict(int),
        }

        def _handle(chunk: pd.DataFrame) -> None:
            prepared = self._prepare_security_data(chunk)
            counts["total_events"] += len(prepared)
            counts["after_hours_sum"] += int(prepared["is_after_hours"].sum())
            counts["weekend_sum"] += int(prepared["is_weekend"].sum())
            for hour, cnt in prepared["hour"].value_counts().items():
                counts["hourly_counts"][int(hour)] += int(cnt)

            group = prepared.groupby("person_id").agg(
                event_count=("event_id", "count"),
                success_sum=("access_granted", "sum"),
            )
            for pid, row in group.iterrows():
                counts["user_event_count"][pid] += int(row["event_count"])
                counts["user_success_sum"][pid] += int(row["success_sum"])

            failures = prepared[prepared["access_granted"] == 0]
            counts["failure_count"] += len(failures)
            for pid, cnt in failures["person_id"].value_counts().items():
                counts["failure_users"][pid] += int(cnt)

        self.chunk_processor.process_dataframe_chunked(df, _handle)

        return self._compile_patterns(
            counts["total_events"],
            counts["after_hours_sum"],
            counts["weekend_sum"],
            counts["hourly_counts"],
            counts["user_event_count"],
            counts["user_success_sum"],
            counts["failure_count"],
            counts["failure_users"],
        )

    # Backwards compatible wrapper ------------------------------------
    def _analyze_access_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        return self.safe_analyze_patterns(df)


# Factory function for compatibility
def create_security_analyzer(**kwargs) -> SecurityPatternsAnalyzer:
    """Factory function to create security analyzer"""
    return SecurityPatternsAnalyzer(**kwargs)


# Alias for enhanced version
EnhancedSecurityAnalyzer = SecurityPatternsAnalyzer
create_enhanced_security_analyzer = create_security_analyzer

# Export for compatibility
__all__ = [
    "SecurityPatternsAnalyzer",
    "create_security_analyzer",
    "EnhancedSecurityAnalyzer",
    "PaginatedAnalyzer",
    "SecurityCallbackController",
    "SecurityEvent",
    "setup_isolated_security_testing",
]


def setup_isolated_security_testing(
    register_handler: bool = False,
) -> tuple[SecurityCallbackController, Optional[Callable[[Dict[str, Any]], None]]]:
    """Return a cleared controller and optional test handler."""

    controller = SecurityCallbackController()
    controller._callbacks.clear()
    controller.history = []
    handler: Optional[Callable[[Dict[str, Any]], None]] = None

    if register_handler:

        def _handler(
            data: Dict[str, Any], event: SecurityEvent = SecurityEvent.ANALYSIS_COMPLETE
        ) -> None:
            controller.history.append((event, data))

        handler = _handler
        for event in SecurityEvent:
            controller.register_handler(event, lambda d, e=event: _handler(d, e))

    return controller, handler
