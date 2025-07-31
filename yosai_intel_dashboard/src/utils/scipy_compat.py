"""Statistical anomaly detection with enhanced error handling and Unicode safety."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from validation.data_validator import DataValidator, DataValidatorProtocol
from validation.unicode_validator import UnicodeValidator

logger = logging.getLogger(__name__)

__all__ = [
    "detect_frequency_anomalies",
    "detect_statistical_anomalies",
    "calculate_severity_from_zscore",
    "get_stats_module",
    "sanitize_unicode_data",
]


_validator = UnicodeValidator()


def sanitize_unicode_data(data: Any) -> Any:
    """Sanitize data recursively using :class:`UnicodeValidator`."""

    if isinstance(data, str):
        return _validator.validate_text(data)
    if isinstance(data, dict):
        return {key: sanitize_unicode_data(value) for key, value in data.items()}
    if isinstance(data, list):
        return [sanitize_unicode_data(item) for item in data]
    if isinstance(data, tuple):
        return tuple(sanitize_unicode_data(item) for item in data)
    return data


class StatisticalAnomalyDetector:
    """Modular statistical anomaly detector with Unicode safety."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        validator: DataValidatorProtocol | None = None,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.validator: DataValidatorProtocol = validator or DataValidator(
            required_columns=["timestamp", "person_id"]
        )

    def _safe_zscore_calculation(self, data: np.ndarray) -> np.ndarray:
        """Calculate Z-scores with error handling."""
        try:
            # Ensure data is numeric
            data = np.asarray(data, dtype=float)

            if len(data) < 2:
                return np.zeros_like(data)

            # Remove infinite values
            finite_mask = np.isfinite(data)
            if not np.any(finite_mask):
                return np.zeros_like(data)

            return stats.zscore(data)

        except Exception as e:
            self.logger.warning(f"Z-score calculation failed: {e}")
            return np.zeros_like(data)

    def _validate_dataframe(self, df: pd.DataFrame) -> bool:
        """Validate ``df`` using the configured :class:`DataValidator`."""

        result = self.validator.validate_dataframe(df)
        if not result.valid:
            self.logger.warning(f"Data validation issues: {result.issues}")
        return result.valid

    def detect_frequency_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect frequency-based anomalies with Unicode safety."""
        result = self.validator.validate_dataframe(df)
        if not result.valid:
            self.logger.warning("; ".join(result.issues or []))
            return []

        anomalies: List[Dict[str, Any]] = []

        try:
            # Sanitize string columns
            df_clean = df.copy()
            for col in df_clean.select_dtypes(include=["object"]).columns:
                df_clean[col] = df_clean[col].apply(sanitize_unicode_data)

            person_stats = (
                df_clean.groupby("person_id")
                .agg(
                    {
                        "timestamp": ["count", "min", "max"],
                        "access_granted": (
                            "sum"
                            if "access_granted" in df_clean.columns
                            else lambda x: len(x)
                        ),
                    }
                )
                .round(2)
            )

            person_stats.columns = [
                "total_attempts",
                "first_access",
                "last_access",
                "successful_attempts",
            ]

            if len(person_stats) < 2:
                return anomalies

            # Use robust percentile-based threshold
            freq_threshold = person_stats["total_attempts"].quantile(0.95)

            if freq_threshold <= 0:
                return anomalies

            high_freq_users = person_stats[
                person_stats["total_attempts"] > freq_threshold
            ]

            for person_id, stats_row in high_freq_users.iterrows():
                # Calculate Z-score for this user's frequency
                all_frequencies = person_stats["total_attempts"].values
                z_scores = self._safe_zscore_calculation(all_frequencies)
                user_idx = person_stats.index.get_loc(person_id)
                user_zscore = z_scores[user_idx] if user_idx < len(z_scores) else 0

                anomaly_data = {
                    "type": "activity_burst",
                    "user_id": sanitize_unicode_data(str(person_id)),
                    "details": {
                        "total_attempts": int(stats_row["total_attempts"]),
                        "successful_attempts": int(stats_row["successful_attempts"]),
                        "time_span": sanitize_unicode_data(
                            str(stats_row["last_access"] - stats_row["first_access"])
                        ),
                        "z_score": float(user_zscore),
                    },
                    "severity": calculate_severity_from_zscore(abs(user_zscore)),
                    "confidence": min(0.95, abs(user_zscore) / 4.0),
                    "timestamp": datetime.now(),
                }

                anomalies.append(sanitize_unicode_data(anomaly_data))

        except Exception as exc:
            self.logger.warning(f"Frequency anomaly detection failed: {exc}")

        return anomalies

    def detect_statistical_anomalies(
        self, df: pd.DataFrame, sensitivity: float
    ) -> List[Dict[str, Any]]:
        """Detect statistical anomalies using Z-score and IQR methods with Unicode safety."""
        result = self.validator.validate_dataframe(df)
        if not result.valid:
            self.logger.warning("; ".join(result.issues or []))
            return []
        anomalies: List[Dict[str, Any]] = []

        try:
            # Sanitize DataFrame
            df_clean = df.copy()
            for col in df_clean.select_dtypes(include=["object"]).columns:
                df_clean[col] = df_clean[col].apply(sanitize_unicode_data)

            # Ensure timestamp is datetime
            if not pd.api.types.is_datetime64_any_dtype(df_clean["timestamp"]):
                df_clean["timestamp"] = pd.to_datetime(
                    df_clean["timestamp"], errors="coerce"
                )

            # Remove rows with invalid timestamps
            df_clean = df_clean.dropna(subset=["timestamp"])

            if len(df_clean) < 5:  # Need minimum data for statistics
                return anomalies

            # Hourly access pattern analysis
            hourly_access = df_clean.groupby(df_clean["timestamp"].dt.hour).size()

            if len(hourly_access) < 2:
                return anomalies

            # Calculate Z-scores for hourly patterns
            z_scores = self._safe_zscore_calculation(hourly_access.values)

            # Adaptive threshold based on sensitivity
            threshold = 3.0 * (1 - sensitivity) if sensitivity > 0 else 3.0
            threshold = max(2.0, min(5.0, threshold))  # Clamp between 2-5

            anomalous_hours = hourly_access[np.abs(z_scores) > threshold]

            for hour, count in anomalous_hours.items():
                hour_idx = hourly_access.index.get_loc(hour)
                z_score = z_scores[hour_idx] if hour_idx < len(z_scores) else 0

                anomaly_data = {
                    "type": "unusual_hour_activity",
                    "details": {
                        "hour": int(hour),
                        "access_count": int(count),
                        "z_score": float(z_score),
                        "threshold_used": float(threshold),
                    },
                    "severity": calculate_severity_from_zscore(abs(z_score)),
                    "confidence": min(0.95, abs(z_score) / 4.0),
                    "timestamp": datetime.now(),
                }

                anomalies.append(sanitize_unicode_data(anomaly_data))

        except Exception as exc:
            self.logger.warning(f"Statistical anomaly detection failed: {exc}")

        return anomalies


class FallbackStats:
    @staticmethod
    def zscore(a, axis=0, ddof=0, nan_policy="propagate"):
        a = np.asarray(a)
        if axis is None:
            a = a.ravel()
            axis = 0
        mean = np.mean(a, axis=axis, keepdims=True)
        std = np.std(a, axis=axis, ddof=ddof, keepdims=True)
        with np.errstate(divide="ignore", invalid="ignore"):
            z = (a - mean) / std
            z = np.where(std == 0, 0, z)
        return z


def get_stats_module():
    try:
        from scipy import stats

        return stats
    except Exception as exc:
        logger.warning(f"scipy.stats unavailable: {exc}")
        return FallbackStats()


stats = get_stats_module()


def calculate_severity_from_zscore(z_score: float) -> str:
    """Calculate severity level from Z-score with input validation."""
    try:
        z_score = float(abs(z_score))

        if z_score >= 4.0:
            return "critical"
        elif z_score >= 3.5:
            return "high"
        elif z_score >= 3.0:
            return "medium"
        else:
            return "low"
    except (ValueError, TypeError):
        return "low"


# Backwards compatibility functions
def detect_frequency_anomalies(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> List[Dict[str, Any]]:
    """Detect frequency-based anomalies (backwards compatible interface)."""
    detector = StatisticalAnomalyDetector(logger)
    return detector.detect_frequency_anomalies(df)


def detect_statistical_anomalies(
    df: pd.DataFrame, sensitivity: float, logger: Optional[logging.Logger] = None
) -> List[Dict[str, Any]]:
    """Detect statistical anomalies (backwards compatible interface)."""
    detector = StatisticalAnomalyDetector(logger)
    return detector.detect_statistical_anomalies(df, sensitivity)
