#!/usr/bin/env python3
"""
Unified Anomaly Detection System - FIXED IMPLEMENTATION
Addresses: Class naming conflicts, memory management, callback consolidation
"""

from __future__ import annotations

import logging
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Protocol, Union

import numpy as np
import pandas as pd

from security_callback_controller import SecurityCallbackController, SecurityEvent
from utils.sklearn_compat import optional_import

# Safe imports with fallbacks
IsolationForest = optional_import("sklearn.ensemble.IsolationForest")
StandardScaler = optional_import("sklearn.preprocessing.StandardScaler")

if IsolationForest is None:

    class IsolationForest:
        def __init__(self, *args, **kwargs):
            raise ImportError("scikit-learn required for ML-based anomaly detection")

        def fit_predict(self, X):
            return np.array([1] * len(X))  # No anomalies fallback


if StandardScaler is None:

    class StandardScaler:
        def fit_transform(self, X):
            return X

        def transform(self, X):
            return X


@dataclass
class AnomalyConfig:
    """Centralized configuration for anomaly detection"""

    contamination: float = 0.1
    sensitivity: float = 0.95
    chunk_size: int = 50_000
    max_memory_mb: int = 500
    enable_ml_detection: bool = True
    enable_statistical_detection: bool = True
    enable_pattern_detection: bool = True
    max_workers: int = 4


class MemoryManager:
    """Memory-safe processing manager"""

    def __init__(self, max_memory_mb: int = 500):
        self.max_memory_mb = max_memory_mb
        self.logger = logging.getLogger(__name__)

    def estimate_dataframe_memory(self, df: pd.DataFrame) -> float:
        """Estimate DataFrame memory usage in MB"""
        try:
            return df.memory_usage(deep=True).sum() / (1024 * 1024)
        except Exception:
            # Fallback estimation
            return len(df) * len(df.columns) * 8 / (1024 * 1024)

    def should_chunk(self, df: pd.DataFrame) -> bool:
        """Determine if DataFrame should be processed in chunks"""
        estimated_mb = self.estimate_dataframe_memory(df)
        return estimated_mb > self.max_memory_mb

    def calculate_chunk_size(self, df: pd.DataFrame) -> int:
        """Calculate optimal chunk size based on memory constraints"""
        estimated_mb = self.estimate_dataframe_memory(df)
        if estimated_mb <= self.max_memory_mb:
            return len(df)

        # Calculate chunk size to stay under memory limit
        ratio = self.max_memory_mb / estimated_mb
        return max(1000, int(len(df) * ratio * 0.8))  # 20% buffer


@dataclass
class AnomalyResult:
    """Standardized anomaly detection result"""

    total_anomalies: int
    severity_distribution: Dict[str, int]
    detection_summary: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    processing_metadata: Dict[str, Any]


class AnomalyDetector:
    """
    UNIFIED Anomaly Detection System

    Fixes:
    - Single canonical class name (no more AnomalyDetection conflicts)
    - Memory-safe chunked processing
    - Consolidated callback system
    - Enterprise security patterns
    """

    def __init__(
        self,
        config: Optional[AnomalyConfig] = None,
        callback_controller: Optional[SecurityCallbackController] = None,
        memory_manager: Optional[MemoryManager] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.config = config or AnomalyConfig()
        self.callbacks = callback_controller or SecurityCallbackController()
        self.memory_manager = memory_manager or MemoryManager(self.config.max_memory_mb)
        self.logger = logger or logging.getLogger(__name__)

        # Initialize ML components if enabled
        if self.config.enable_ml_detection:
            try:
                self.isolation_forest = IsolationForest(
                    contamination=self.config.contamination,
                    random_state=42,
                    n_estimators=100,
                )
                self.scaler = StandardScaler()
            except Exception as e:
                self.logger.warning(f"ML initialization failed: {e}")
                self.config.enable_ml_detection = False

    def detect_anomalies(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Main detection method with legacy API compatibility

        Returns: Legacy format for backward compatibility
        """
        try:
            result = self.analyze_anomalies(df, **kwargs)
            return self._convert_to_legacy_format(result)
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
            self.callbacks.trigger_event(
                SecurityEvent.ANALYSIS_ERROR, {"error": str(e)}
            )
            return self._empty_legacy_result()

    def analyze_anomalies(self, df: pd.DataFrame, **kwargs) -> AnomalyResult:
        """
        Enhanced anomaly detection with memory safety

        Returns: Modern structured result
        """
        try:
            # Validate input
            if df is None or len(df) == 0:
                return self._empty_result()

            # Memory safety check
            if self.memory_manager.should_chunk(df):
                return self._analyze_chunked(df, **kwargs)
            else:
                return self._analyze_full_dataset(df, **kwargs)

        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            self.callbacks.trigger_event(
                SecurityEvent.ANALYSIS_ERROR, {"error": str(e)}
            )
            return self._empty_result()

    def _analyze_chunked(self, df: pd.DataFrame, **kwargs) -> AnomalyResult:
        """Memory-safe chunked analysis"""
        chunk_size = self.memory_manager.calculate_chunk_size(df)
        all_anomalies = []
        total_chunks = len(df) // chunk_size + (1 if len(df) % chunk_size else 0)

        self.logger.info(
            f"Processing {len(df)} rows in {total_chunks} chunks of {chunk_size}"
        )
        self.callbacks.trigger_event(
            SecurityEvent.FILE_PROCESSING_START,
            {
                "total_rows": len(df),
                "chunk_size": chunk_size,
                "total_chunks": total_chunks,
            },
        )

        try:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = []

                for i in range(0, len(df), chunk_size):
                    chunk = df.iloc[i : i + chunk_size].copy()
                    future = executor.submit(
                        self._analyze_chunk, chunk, i // chunk_size
                    )
                    futures.append(future)

                for future in as_completed(futures):
                    try:
                        chunk_anomalies = future.result()
                        all_anomalies.extend(chunk_anomalies)
                    except Exception as e:
                        self.logger.error(f"Chunk processing failed: {e}")

            return self._consolidate_results(
                all_anomalies,
                {
                    "processing_mode": "chunked",
                    "total_chunks": total_chunks,
                    "chunk_size": chunk_size,
                },
            )

        except Exception as e:
            self.logger.error(f"Chunked analysis failed: {e}")
            self.callbacks.trigger_event(
                SecurityEvent.FILE_PROCESSING_ERROR, {"error": str(e)}
            )
            return self._empty_result()

    def _analyze_full_dataset(self, df: pd.DataFrame, **kwargs) -> AnomalyResult:
        """Process entire dataset in memory"""
        try:
            anomalies = self._analyze_chunk(df, 0)
            return self._consolidate_results(
                anomalies, {"processing_mode": "full_dataset", "total_rows": len(df)}
            )
        except Exception as e:
            self.logger.error(f"Full dataset analysis failed: {e}")
            return self._empty_result()

    def _analyze_chunk(
        self, chunk: pd.DataFrame, chunk_id: int
    ) -> List[Dict[str, Any]]:
        """Analyze single chunk for anomalies"""
        anomalies = []

        try:
            # Prepare data
            prepared_data = self._prepare_data(chunk)

            # Statistical detection
            if self.config.enable_statistical_detection:
                stat_anomalies = self._detect_statistical_anomalies(prepared_data)
                anomalies.extend(stat_anomalies)

            # Pattern detection
            if self.config.enable_pattern_detection:
                pattern_anomalies = self._detect_pattern_anomalies(prepared_data)
                anomalies.extend(pattern_anomalies)

            # ML detection
            if self.config.enable_ml_detection:
                ml_anomalies = self._detect_ml_anomalies(prepared_data)
                anomalies.extend(ml_anomalies)

            # Add chunk metadata to anomalies
            for anomaly in anomalies:
                anomaly["chunk_id"] = chunk_id
                anomaly["chunk_size"] = len(chunk)

            return anomalies

        except Exception as e:
            self.logger.error(f"Chunk {chunk_id} analysis failed: {e}")
            return []

    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and validate data for analysis"""
        try:
            # Basic validation
            if df.empty:
                return df

            # Remove duplicates
            df_clean = df.drop_duplicates()

            # Handle missing values
            df_clean = df_clean.dropna()

            return df_clean

        except Exception as e:
            self.logger.error(f"Data preparation failed: {e}")
            return df

    def _detect_statistical_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect statistical anomalies using z-score and IQR"""
        anomalies = []

        try:
            numeric_columns = df.select_dtypes(include=[np.number]).columns

            for col in numeric_columns:
                # Z-score based detection
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                outliers = df[z_scores > 3]  # 3-sigma rule

                for idx, row in outliers.iterrows():
                    anomalies.append(
                        {
                            "type": "statistical",
                            "method": "z_score",
                            "column": col,
                            "value": row[col],
                            "z_score": z_scores.loc[idx],
                            "severity": self._calculate_severity(z_scores.loc[idx]),
                            "confidence": min(0.99, z_scores.loc[idx] / 10),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        except Exception as e:
            self.logger.error(f"Statistical detection failed: {e}")

        return anomalies

    def _detect_pattern_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect pattern-based anomalies"""
        anomalies = []

        try:
            # Frequency-based patterns
            if "person_id" in df.columns:
                person_counts = df["person_id"].value_counts()
                threshold = person_counts.mean() + 3 * person_counts.std()

                high_activity_users = person_counts[person_counts > threshold]

                for person_id, count in high_activity_users.items():
                    anomalies.append(
                        {
                            "type": "pattern",
                            "method": "frequency",
                            "person_id": person_id,
                            "activity_count": int(count),
                            "threshold": float(threshold),
                            "severity": "high" if count > threshold * 2 else "medium",
                            "confidence": 0.85,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        except Exception as e:
            self.logger.error(f"Pattern detection failed: {e}")

        return anomalies

    def _detect_ml_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies using machine learning"""
        anomalies = []

        if not self.config.enable_ml_detection:
            return anomalies

        try:
            # Prepare features for ML
            numeric_features = df.select_dtypes(include=[np.number])

            if len(numeric_features.columns) == 0:
                return anomalies

            # Scale features
            X_scaled = self.scaler.fit_transform(numeric_features)

            # Detect anomalies
            predictions = self.isolation_forest.fit_predict(X_scaled)
            anomaly_scores = self.isolation_forest.decision_function(X_scaled)

            # Process results
            for idx, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
                if pred == -1:  # Anomaly detected
                    anomalies.append(
                        {
                            "type": "ml",
                            "method": "isolation_forest",
                            "index": idx,
                            "anomaly_score": float(score),
                            "severity": self._score_to_severity(score),
                            "confidence": min(0.95, abs(score)),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        except Exception as e:
            self.logger.error(f"ML detection failed: {e}")

        return anomalies

    def _calculate_severity(self, z_score: float) -> str:
        """Calculate severity level from z-score"""
        if z_score > 5:
            return "critical"
        elif z_score > 4:
            return "high"
        elif z_score > 3:
            return "medium"
        else:
            return "low"

    def _score_to_severity(self, score: float) -> str:
        """Convert ML anomaly score to severity level"""
        abs_score = abs(score)
        if abs_score > 0.8:
            return "critical"
        elif abs_score > 0.6:
            return "high"
        elif abs_score > 0.4:
            return "medium"
        else:
            return "low"

    def _consolidate_results(
        self, anomalies: List[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> AnomalyResult:
        """Consolidate anomaly results into structured format"""
        try:
            # Remove duplicates
            unique_anomalies = self._deduplicate_anomalies(anomalies)

            # Calculate statistics
            severity_distribution = self._calculate_severity_distribution(
                unique_anomalies
            )
            detection_summary = self._generate_detection_summary(unique_anomalies)
            risk_assessment = self._assess_risk(unique_anomalies)
            recommendations = self._generate_recommendations(
                unique_anomalies, risk_assessment
            )

            # Emit events
            self.callbacks.trigger_event(
                SecurityEvent.ANOMALY_DETECTED,
                {
                    "count": len(unique_anomalies),
                    "severity_distribution": severity_distribution,
                },
            )

            return AnomalyResult(
                total_anomalies=len(unique_anomalies),
                severity_distribution=severity_distribution,
                detection_summary=detection_summary,
                risk_assessment=risk_assessment,
                recommendations=recommendations,
                processing_metadata=metadata,
            )

        except Exception as e:
            self.logger.error(f"Result consolidation failed: {e}")
            return self._empty_result()

    def _deduplicate_anomalies(
        self, anomalies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate anomalies"""
        if not anomalies:
            return anomalies

        seen = set()
        unique = []

        for anomaly in anomalies:
            # Create deduplication key
            key_parts = [
                anomaly.get("type", ""),
                anomaly.get("method", ""),
                anomaly.get("person_id", ""),
                anomaly.get("column", ""),
                str(anomaly.get("index", "")),
            ]
            key = "|".join(key_parts)

            if key not in seen:
                seen.add(key)
                unique.append(anomaly)

        return unique

    def _calculate_severity_distribution(
        self, anomalies: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate distribution of severity levels"""
        distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for anomaly in anomalies:
            severity = anomaly.get("severity", "low")
            if severity in distribution:
                distribution[severity] += 1

        return distribution

    def _generate_detection_summary(
        self, anomalies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate detection summary"""
        return {
            "total_anomalies": len(anomalies),
            "detection_methods": list(set(a.get("method", "") for a in anomalies)),
            "detection_timestamp": datetime.now().isoformat(),
            "confidence_mean": (
                np.mean([a.get("confidence", 0) for a in anomalies]) if anomalies else 0
            ),
        }

    def _assess_risk(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall risk level"""
        if not anomalies:
            return {"risk_level": "low", "risk_score": 0}

        # Calculate weighted risk score
        severity_weights = {"critical": 10, "high": 7, "medium": 4, "low": 1}
        total_score = sum(
            severity_weights.get(a.get("severity", "low"), 1) for a in anomalies
        )

        # Normalize score
        max_possible = len(anomalies) * 10
        risk_score = (total_score / max_possible) if max_possible > 0 else 0

        # Determine risk level
        if risk_score > 0.8:
            risk_level = "critical"
        elif risk_score > 0.6:
            risk_level = "high"
        elif risk_score > 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "risk_score": float(risk_score),
            "total_weighted_score": total_score,
        }

    def _generate_recommendations(
        self, anomalies: List[Dict[str, Any]], risk_assessment: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if not anomalies:
            recommendations.append("No anomalies detected. Continue monitoring.")
            return recommendations

        severity_dist = self._calculate_severity_distribution(anomalies)

        if severity_dist["critical"] > 0:
            recommendations.append(
                "IMMEDIATE: Investigate critical anomalies requiring urgent attention"
            )

        if severity_dist["high"] > 0:
            recommendations.append(
                "HIGH PRIORITY: Review high-severity anomalies within 24 hours"
            )

        if len(anomalies) > 50:
            recommendations.append(
                "Consider implementing automated response for high-volume anomalies"
            )

        # Method-specific recommendations
        methods = set(a.get("method", "") for a in anomalies)
        if "frequency" in methods:
            recommendations.append(
                "Monitor user activity patterns for potential insider threats"
            )

        if "isolation_forest" in methods:
            recommendations.append("Review ML-detected anomalies for false positives")

        return recommendations

    def _convert_to_legacy_format(self, result: AnomalyResult) -> Dict[str, Any]:
        """Convert modern result to legacy format for backward compatibility"""
        return {
            "anomalies_detected": result.total_anomalies,
            "threat_level": result.risk_assessment.get("risk_level", "low"),
            "severity_distribution": result.severity_distribution,
            "detection_summary": result.detection_summary,
            "risk_assessment": result.risk_assessment,
            "recommendations": result.recommendations,
            "processing_metadata": result.processing_metadata,
        }

    def _empty_result(self) -> AnomalyResult:
        """Return empty result structure"""
        return AnomalyResult(
            total_anomalies=0,
            severity_distribution={"critical": 0, "high": 0, "medium": 0, "low": 0},
            detection_summary={
                "total_anomalies": 0,
                "message": "No data to analyze",
                "detection_timestamp": datetime.now().isoformat(),
            },
            risk_assessment={"risk_level": "low", "risk_score": 0},
            recommendations=["No anomalies detected"],
            processing_metadata={"status": "empty"},
        )

    def _empty_legacy_result(self) -> Dict[str, Any]:
        """Return empty result in legacy format"""
        return {
            "anomalies_detected": 0,
            "threat_level": "unknown",
            "severity_distribution": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "detection_summary": {
                "total_anomalies": 0,
                "message": "Error in detection",
            },
            "risk_assessment": {"risk_level": "error", "risk_score": 0},
            "recommendations": ["Unable to perform anomaly detection"],
            "processing_metadata": {"status": "error"},
        }


# Factory functions for backward compatibility
def create_anomaly_detector(config: Optional[AnomalyConfig] = None) -> AnomalyDetector:
    """Factory function to create anomaly detector"""
    return AnomalyDetector(config=config)


# Legacy aliases for migration support
AnomalyDetection = AnomalyDetector  # DEPRECATED: Use AnomalyDetector
EnhancedAnomalyDetector = AnomalyDetector


# Export interface
__all__ = [
    "AnomalyDetector",
    "AnomalyConfig",
    "AnomalyResult",
    "SecurityCallbackController",
    "MemoryManager",
    "create_anomaly_detector",
]
