"""
Fix for analytics/anomaly_detection.py
Replace the existing file with this corrected version that exports AnomalyDetection
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import DataConversionWarning
from scipy import stats
import logging
from dataclasses import dataclass
import warnings

# Ignore benign type conversion warnings emitted by scikit-learn when integer
# features are automatically cast to floats.
warnings.filterwarnings(
    "ignore",
    category=DataConversionWarning,
    module="sklearn",
)

logger = logging.getLogger(__name__)


@dataclass
class AnomalyAnalysis:
    """Comprehensive anomaly analysis result"""
    total_anomalies: int
    severity_distribution: Dict[str, int]
    detection_summary: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]


class AnomalyDetector:
    """Enhanced anomaly detector using multiple algorithms and statistical methods"""

    def __init__(
        self,
        contamination: float = 0.1,
        sensitivity: float = 0.95,
        logger: Optional[logging.Logger] = None,
    ):
        self.contamination = contamination
        self.sensitivity = sensitivity
        self.logger = logger or logging.getLogger(__name__)

        # Initialize ML models
        self.isolation_forest = IsolationForest(
            contamination=contamination, random_state=42, n_estimators=100
        )
        self.scaler = StandardScaler()

    def detect_anomalies(
        self, df: pd.DataFrame, sensitivity: Optional[float] = None
    ) -> Dict[str, Any]:
        """Main anomaly detection method with legacy compatibility"""
        try:
            result = self.analyze_anomalies(df, sensitivity)
            return self._convert_to_legacy_format(result)
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
            return self._empty_legacy_result()

    def analyze_anomalies(
        self, df: pd.DataFrame, sensitivity: Optional[float] = None
    ) -> AnomalyAnalysis:
        """Enhanced anomaly detection method"""
        try:
            # Use provided sensitivity or default
            detection_sensitivity = sensitivity or self.sensitivity

            # Prepare data for anomaly detection
            df_clean = self._prepare_anomaly_data(df)

            if len(df_clean) < 10:
                return self._insufficient_data_result()

            # Multi-method anomaly detection
            all_anomalies = []

            # Statistical anomaly detection
            statistical_anomalies = self._detect_statistical_anomalies(
                df_clean, detection_sensitivity
            )
            all_anomalies.extend(statistical_anomalies)

            # Pattern-based anomaly detection
            pattern_anomalies = self._detect_pattern_anomalies(
                df_clean, detection_sensitivity
            )
            all_anomalies.extend(pattern_anomalies)

            # ML-based anomaly detection
            ml_anomalies = self._detect_ml_anomalies(df_clean, detection_sensitivity)
            all_anomalies.extend(ml_anomalies)

            # Remove duplicates
            unique_anomalies = self._deduplicate_anomalies(all_anomalies)

            # Generate analysis summaries
            severity_distribution = self._calculate_severity_distribution(unique_anomalies)
            detection_summary = self._generate_detection_summary(unique_anomalies)
            risk_assessment = self._assess_overall_risk(unique_anomalies)
            recommendations = self._generate_recommendations(unique_anomalies, risk_assessment)

            return AnomalyAnalysis(
                total_anomalies=len(unique_anomalies),
                severity_distribution=severity_distribution,
                detection_summary=detection_summary,
                risk_assessment=risk_assessment,
                recommendations=recommendations,
            )

        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
            return self._empty_anomaly_analysis()

    def _prepare_anomaly_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and clean data for anomaly detection"""
        df_clean = df.copy()

        # Handle Unicode issues
        string_columns = df_clean.select_dtypes(include=["object"]).columns
        for col in string_columns:
            df_clean[col] = (
                df_clean[col]
                .astype(str)
                .apply(lambda x: x.encode("utf-8", errors="ignore").decode("utf-8"))
            )

        # Ensure required columns exist or create defaults
        required_cols = ["timestamp", "person_id", "door_id", "access_result"]
        for col in required_cols:
            if col not in df_clean.columns:
                if col == "timestamp":
                    df_clean[col] = pd.Timestamp.now()
                elif col in ["person_id", "door_id"]:
                    df_clean[col] = f"unknown_{col}"
                elif col == "access_result":
                    df_clean[col] = "Unknown"

        # Convert timestamp
        if not pd.api.types.is_datetime64_any_dtype(df_clean["timestamp"]):
            try:
                df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"])
            except:
                df_clean["timestamp"] = pd.Timestamp.now()

        # Add derived features
        df_clean["hour"] = df_clean["timestamp"].dt.hour
        df_clean["day_of_week"] = df_clean["timestamp"].dt.dayofweek
        df_clean["is_weekend"] = df_clean["day_of_week"].isin([5, 6])
        df_clean["is_after_hours"] = df_clean["hour"].isin(
            list(range(0, 6)) + list(range(22, 24))
        )
        df_clean["access_granted"] = (df_clean["access_result"] == "Granted").astype(int)

        return df_clean

    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Alias for backward compatibility"""
        return self._prepare_anomaly_data(df)

    def _detect_frequency_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect frequency-based anomalies"""
        anomalies = []
        
        try:
            # Group by person and analyze access frequency
            person_stats = df.groupby('person_id').agg({
                'timestamp': ['count', 'min', 'max'],
                'access_granted': 'sum'
            }).round(2)
            
            person_stats.columns = ['total_attempts', 'first_access', 'last_access', 'successful_attempts']
            
            # Detect high-frequency users (activity bursts)
            freq_threshold = person_stats['total_attempts'].quantile(0.95)
            high_freq_users = person_stats[person_stats['total_attempts'] > freq_threshold]
            
            for person_id, stats in high_freq_users.iterrows():
                anomalies.append({
                    "type": "activity_burst",
                    "user_id": person_id,
                    "details": {
                        "total_attempts": int(stats['total_attempts']),
                        "successful_attempts": int(stats['successful_attempts']),
                        "time_span": str(stats['last_access'] - stats['first_access'])
                    },
                    "severity": "medium",
                    "confidence": 0.8,
                    "timestamp": datetime.now()
                })
                
        except Exception as e:
            self.logger.warning(f"Frequency anomaly detection failed: {e}")
            
        return anomalies

    def _detect_statistical_anomalies(self, df: pd.DataFrame, sensitivity: float) -> List[Dict[str, Any]]:
        """Detect statistical anomalies using Z-score and IQR methods"""
        anomalies = []
        
        try:
            # Access frequency anomalies
            hourly_access = df.groupby(df['timestamp'].dt.hour).size()
            z_scores = np.abs(stats.zscore(hourly_access))
            
            anomalous_hours = hourly_access[z_scores > (3.0 * (1 - sensitivity))]
            
            for hour, count in anomalous_hours.items():
                anomalies.append({
                    "type": "unusual_hour_activity",
                    "details": {
                        "hour": int(hour),
                        "access_count": int(count),
                        "z_score": float(z_scores[hour])
                    },
                    "severity": self._calculate_severity_from_zscore(z_scores[hour]),
                    "confidence": min(0.95, abs(z_scores[hour]) / 4.0),
                    "timestamp": datetime.now()
                })
                
        except Exception as e:
            self.logger.warning(f"Statistical anomaly detection failed: {e}")
            
        return anomalies

    def _detect_pattern_anomalies(self, df: pd.DataFrame, sensitivity: float) -> List[Dict[str, Any]]:
        """Detect pattern-based anomalies"""
        anomalies = []
        
        try:
            # After-hours access patterns
            after_hours_access = df[df['is_after_hours']]
            if len(after_hours_access) > 0:
                after_hours_users = after_hours_access.groupby('person_id').size()
                threshold = max(1, int(len(after_hours_users) * (1 - sensitivity)))
                
                frequent_after_hours = after_hours_users[after_hours_users > threshold]
                
                for person_id, count in frequent_after_hours.items():
                    anomalies.append({
                        "type": "frequent_after_hours",
                        "user_id": person_id,
                        "details": {
                            "after_hours_count": int(count),
                            "total_access_count": int(df[df['person_id'] == person_id].shape[0])
                        },
                        "severity": "medium",
                        "confidence": 0.7,
                        "timestamp": datetime.now()
                    })
                    
        except Exception as e:
            self.logger.warning(f"Pattern anomaly detection failed: {e}")
            
        return anomalies

    def _detect_ml_anomalies(self, df: pd.DataFrame, sensitivity: float) -> List[Dict[str, Any]]:
        """Detect anomalies using machine learning"""
        anomalies = []
        
        try:
            # Prepare features for ML
            features = ['hour', 'day_of_week', 'is_weekend', 'is_after_hours', 'access_granted']
            feature_df = df[features].copy()
            
            if len(feature_df) < 10:
                return anomalies
                
            # Fit isolation forest
            self.isolation_forest.set_params(contamination=1 - sensitivity)
            outliers = self.isolation_forest.fit_predict(feature_df)
            
            # Get anomaly indices
            anomaly_indices = np.where(outliers == -1)[0]
            
            for idx in anomaly_indices:
                original_row = df.iloc[idx]
                anomalies.append({
                    "type": "ml_anomaly",
                    "details": {
                        "person_id": original_row["person_id"],
                        "door_id": original_row["door_id"],
                        "timestamp": original_row["timestamp"].isoformat(),
                        "features": feature_df.iloc[idx].to_dict(),
                    },
                    "severity": "medium",
                    "confidence": 0.6,
                    "timestamp": datetime.now()
                })
                
        except Exception as e:
            self.logger.warning(f"ML anomaly detection failed: {e}")
            
        return anomalies

    def _calculate_severity_from_zscore(self, z_score: float) -> str:
        """Calculate severity level from Z-score"""
        if z_score >= 4.0:
            return "critical"
        elif z_score >= 3.5:
            return "high"
        elif z_score >= 3.0:
            return "medium"
        else:
            return "low"

    def _deduplicate_anomalies(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate anomalies"""
        if not anomalies:
            return anomalies

        seen_combinations = set()
        unique_anomalies = []

        for anomaly in anomalies:
            # Create a key for deduplication
            anomaly_type = anomaly.get("type", "unknown")
            user_id = anomaly.get("user_id", anomaly.get("details", {}).get("person_id", "unknown"))
            dedup_key = (anomaly_type, user_id)

            if dedup_key not in seen_combinations:
                seen_combinations.add(dedup_key)
                unique_anomalies.append(anomaly)

        return unique_anomalies

    def _calculate_severity_distribution(self, anomalies: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate distribution of anomalies by severity"""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for anomaly in anomalies:
            severity = anomaly.get("severity", "low")
            severity_counts[severity] += 1

        return severity_counts

    def _generate_detection_summary(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate detection summary"""
        return {
            "total_anomalies": len(anomalies),
            "anomaly_types": list(set(a.get("type", "unknown") for a in anomalies)),
            "average_confidence": np.mean([a.get("confidence", 0) for a in anomalies]) if anomalies else 0,
            "detection_timestamp": datetime.now().isoformat()
        }

    def _assess_overall_risk(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall risk level"""
        if not anomalies:
            return {"risk_level": "low", "risk_score": 0}

        severity_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        total_score = sum(severity_weights.get(a.get("severity", "low"), 1) for a in anomalies)
        max_possible_score = len(anomalies) * 4

        risk_score = total_score / max_possible_score if max_possible_score > 0 else 0

        if risk_score >= 0.7:
            risk_level = "critical"
        elif risk_score >= 0.5:
            risk_level = "high"
        elif risk_score >= 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {"risk_level": risk_level, "risk_score": risk_score}

    def _generate_recommendations(self, anomalies: List[Dict[str, Any]], risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on anomalies"""
        recommendations = []

        if not anomalies:
            recommendations.append("No anomalies detected. Continue monitoring.")
            return recommendations

        # Type-specific recommendations
        anomaly_types = set(a.get("type", "unknown") for a in anomalies)

        if "activity_burst" in anomaly_types:
            recommendations.append("Investigate users with unusually high access frequency")

        if "frequent_after_hours" in anomaly_types:
            recommendations.append("Review after-hours access policies and permissions")

        if "unusual_hour_activity" in anomaly_types:
            recommendations.append("Analyze access patterns during unusual hours")

        # Risk-based recommendations
        risk_level = risk_assessment.get("risk_level", "low")
        if risk_level in ["critical", "high"]:
            recommendations.append("Immediate security review recommended")
        elif risk_level == "medium":
            recommendations.append("Enhanced monitoring suggested")

        return recommendations

    def _convert_to_legacy_format(self, analysis: AnomalyAnalysis) -> Dict[str, Any]:
        """Convert modern analysis to legacy format for backward compatibility"""
        return {
            "anomalies_detected": analysis.total_anomalies,
            "threat_level": analysis.risk_assessment.get("risk_level", "unknown"),
            "severity_distribution": analysis.severity_distribution,
            "detection_summary": analysis.detection_summary,
            "risk_assessment": analysis.risk_assessment,
            "recommendations": analysis.recommendations,
            "statistical_anomalies": [],
            "pattern_anomalies": [],
            "ml_anomalies": [],
            "anomaly_count": analysis.total_anomalies,
            "confidence_mean": analysis.detection_summary.get("average_confidence", 0),
        }

    def _insufficient_data_result(self) -> AnomalyAnalysis:
        """Return result for insufficient data"""
        return AnomalyAnalysis(
            total_anomalies=0,
            severity_distribution={"critical": 0, "high": 0, "medium": 0, "low": 0},
            detection_summary={
                "total_anomalies": 0,
                "message": "Insufficient data for anomaly detection (minimum 10 records required)",
                "detection_timestamp": datetime.now().isoformat()
            },
            risk_assessment={"risk_level": "unknown", "risk_score": 0},
            recommendations=["Collect more data for meaningful anomaly detection"],
        )

    def _empty_anomaly_analysis(self) -> AnomalyAnalysis:
        """Return empty analysis result"""
        return AnomalyAnalysis(
            total_anomalies=0,
            severity_distribution={"critical": 0, "high": 0, "medium": 0, "low": 0},
            detection_summary={
                "total_anomalies": 0,
                "message": "Error in anomaly detection",
                "detection_timestamp": datetime.now().isoformat()
            },
            risk_assessment={"risk_level": "error", "risk_score": 0},
            recommendations=["Unable to perform anomaly detection due to data issues"],
        )

    def _empty_legacy_result(self) -> Dict[str, Any]:
        """Return empty result in legacy format"""
        return {
            "anomalies_detected": 0,
            "threat_level": "unknown",
            "severity_distribution": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "detection_summary": {
                "total_anomalies": 0,
                "message": "Error in anomaly detection",
            },
            "risk_assessment": {"risk_level": "error", "risk_score": 0},
            "recommendations": ["Unable to perform anomaly detection due to data issues"],
            "statistical_anomalies": [],
            "pattern_anomalies": [],
            "ml_anomalies": [],
            "anomaly_count": 0,
            "confidence_mean": 0,
        }


# Backward compatibility aliases
AnomalyDetection = AnomalyDetector  # This fixes the import error!


# Factory functions for compatibility
def create_anomaly_detector(**kwargs) -> AnomalyDetector:
    """Factory function to create anomaly detector"""
    return AnomalyDetector(**kwargs)


# Enhanced version alias
EnhancedAnomalyDetector = AnomalyDetector
create_enhanced_anomaly_detector = create_anomaly_detector

# Export all necessary classes and functions
__all__ = [
    "AnomalyDetector", 
    "AnomalyDetection",  # Key export for backward compatibility
    "AnomalyAnalysis",
    "create_anomaly_detector", 
    "EnhancedAnomalyDetector"
]
