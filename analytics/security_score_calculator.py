"""Security Score Calculation Module
Corrects mathematical errors in security metrics calculation"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from pandas import Series, DataFrame

# Unicode-safe string handling
from security.unicode_security_handler import UnicodeSecurityHandler


@dataclass
class SecurityCalculationConfig:
    """Configuration for security calculations with validation"""

    baseline_failed_rate: float = 0.05
    baseline_badge_issue_rate: float = 0.02
    baseline_after_hours_rate: float = 0.05
    baseline_weekend_rate: float = 0.25

    # Standard deviations for z-score calculation
    std_failed_rate: float = 0.02
    std_badge_issue_rate: float = 0.01
    std_after_hours_rate: float = 0.02
    std_weekend_rate: float = 0.05

    # Weights (must sum to 1.0)
    weight_failed: float = 0.3
    weight_badge: float = 0.25
    weight_after_hours: float = 0.2
    weight_weekend: float = 0.25

    def __post_init__(self):
        weights_sum = (
            self.weight_failed
            + self.weight_badge
            + self.weight_after_hours
            + self.weight_weekend
        )
        if abs(weights_sum - 1.0) > 1e-10:
            raise ValueError(f"Weights must sum to 1.0, got {weights_sum}")


class SecurityScoreCalculator:
    """Fixed security score calculator with proper statistical methods"""

    def __init__(self, config: Optional[SecurityCalculationConfig] = None):
        self.config = config or SecurityCalculationConfig()
        self.logger = logging.getLogger(__name__)

    def sanitize_unicode_text(self, text: str) -> str:
        """Sanitize ``text`` using the shared security handler."""
        return UnicodeSecurityHandler.sanitize_unicode_input(text)

    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Validate required columns exist and add missing ones"""
        required_cols = ["access_result", "badge_status", "timestamp"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            return False, f"Missing required columns: {missing_cols}"

        if "is_after_hours" not in df.columns:
            df["is_after_hours"] = self._calculate_after_hours(df["timestamp"])

        if "is_weekend" not in df.columns:
            df["is_weekend"] = pd.to_datetime(df["timestamp"]).dt.weekday >= 5

        return True, "Validation passed"

    def _calculate_after_hours(self, timestamps: Series) -> Series:
        """Calculate after hours flag (before 8 AM or after 6 PM)"""
        dt_series = pd.to_datetime(timestamps)
        hour = dt_series.dt.hour
        return (hour < 8) | (hour >= 18)

    def calculate_base_rates(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate base security rates with error handling"""
        if df.empty:
            return {
                "failed_rate": 0.0,
                "badge_issue_rate": 0.0,
                "after_hours_rate": 0.0,
                "weekend_rate": 0.0,
            }

        total_records = len(df)

        failed_rate = len(df[df["access_result"] == "Denied"]) / total_records
        badge_issue_rate = len(df[df["badge_status"] != "Valid"]) / total_records
        after_hours_rate = len(df[df["is_after_hours"]]) / total_records
        weekend_rate = len(df[df["is_weekend"]]) / total_records

        return {
            "failed_rate": failed_rate,
            "badge_issue_rate": badge_issue_rate,
            "after_hours_rate": after_hours_rate,
            "weekend_rate": weekend_rate,
        }

    def calculate_security_score_fixed(self, df: pd.DataFrame) -> Dict[str, any]:
        """Fixed security score calculation with proper statistical methods"""
        is_valid, message = self.validate_dataframe(df)
        if not is_valid:
            self.logger.error(f"Data validation failed: {message}")
            return self._empty_score_result(f"Validation error: {message}")

        if df.empty:
            return self._empty_score_result("Empty dataset")

        try:
            rates = self.calculate_base_rates(df)
            z_scores = self._calculate_z_scores(rates)
            score = self._calculate_weighted_score(z_scores)
            confidence_interval = self._calculate_proper_confidence_interval(
                rates, len(df)
            )
            threat_level = self._determine_threat_level(score)

            return {
                "score": float(score),
                "threat_level": threat_level,
                "confidence_interval": confidence_interval,
                "method": "corrected_weighted_zscore",
                "base_rates": rates,
                "z_scores": z_scores,
            }

        except Exception as e:
            self.logger.error(f"Security score calculation failed: {e}")
            return self._empty_score_result(f"Calculation error: {str(e)}")

    def _calculate_z_scores(self, rates: Dict[str, float]) -> Dict[str, float]:
        """Calculate z-scores for each security metric"""
        z_scores = {}

        if self.config.std_failed_rate > 0:
            z_scores["failed"] = (
                rates["failed_rate"] - self.config.baseline_failed_rate
            ) / self.config.std_failed_rate
        else:
            z_scores["failed"] = 0.0

        if self.config.std_badge_issue_rate > 0:
            z_scores["badge"] = (
                rates["badge_issue_rate"] - self.config.baseline_badge_issue_rate
            ) / self.config.std_badge_issue_rate
        else:
            z_scores["badge"] = 0.0

        if self.config.std_after_hours_rate > 0:
            z_scores["after_hours"] = (
                rates["after_hours_rate"] - self.config.baseline_after_hours_rate
            ) / self.config.std_after_hours_rate
        else:
            z_scores["after_hours"] = 0.0

        if self.config.std_weekend_rate > 0:
            z_scores["weekend"] = (
                rates["weekend_rate"] - self.config.baseline_weekend_rate
            ) / self.config.std_weekend_rate
        else:
            z_scores["weekend"] = 0.0

        return z_scores

    def _calculate_weighted_score(self, z_scores: Dict[str, float]) -> float:
        """Calculate weighted security score from z-scores"""
        penalties = {
            "failed": max(0, z_scores["failed"]) * self.config.weight_failed,
            "badge": max(0, z_scores["badge"]) * self.config.weight_badge,
            "after_hours": max(0, z_scores["after_hours"])
            * self.config.weight_after_hours,
            "weekend": max(0, z_scores["weekend"]) * self.config.weight_weekend,
        }

        total_penalty = sum(penalties.values())
        max_penalty = 3.0  # Corresponds to 3 sigma
        normalized_penalty = min(total_penalty / max_penalty, 1.0)
        score = 100.0 * (1.0 - normalized_penalty)
        return max(0.0, min(100.0, score))

    def _calculate_proper_confidence_interval(
        self, rates: Dict[str, float], n_samples: int
    ) -> Tuple[float, float]:
        """Calculate proper confidence interval using binomial proportion statistics"""
        if n_samples < 30:
            return (0.0, 100.0)

        p = rates["failed_rate"]
        z = 1.96  # 95% confidence
        denominator = 1 + (z**2 / n_samples)
        center = (p + (z**2 / (2 * n_samples))) / denominator
        margin = (z / denominator) * np.sqrt(
            (p * (1 - p) / n_samples) + (z**2 / (4 * n_samples**2))
        )

        lower_bound = max(0.0, center - margin)
        upper_bound = min(1.0, center + margin)

        score_lower = 100.0 * (1.0 - upper_bound)
        score_upper = 100.0 * (1.0 - lower_bound)

        score_lower = max(0.0, min(100.0, score_lower))
        score_upper = max(0.0, min(100.0, score_upper))

        return (score_lower, score_upper)

    def _determine_threat_level(self, score: float) -> str:
        if score >= 90:
            return "low"
        elif score >= 70:
            return "medium"
        elif score >= 50:
            return "high"
        else:
            return "critical"

    def _empty_score_result(self, reason: str = "No data") -> Dict[str, any]:
        return {
            "score": 0.0,
            "threat_level": "unknown",
            "confidence_interval": (0.0, 0.0),
            "method": "none",
            "error": reason,
            "base_rates": {},
            "z_scores": {},
        }


def create_security_calculator(
    config: Optional[SecurityCalculationConfig] = None,
) -> SecurityScoreCalculator:
    """Create security calculator instance"""
    return SecurityScoreCalculator(config)


__all__ = [
    "SecurityScoreCalculator",
    "SecurityCalculationConfig",
    "create_security_calculator",
]
