"""
Enhanced Access Trends Analyzer
Replace the entire content of analytics/access_trends.py with this code
"""

import logging
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from utils.sklearn_compat import optional_import

LinearRegression = optional_import("sklearn.linear_model.LinearRegression")

if LinearRegression is None:  # pragma: no cover - fallback
    class LinearRegression:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError("scikit-learn is required for LinearRegression")

# Suppress pandas deprecation warnings regarding legacy frequency strings.
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    module="pandas",
)


@dataclass
class TrendAnalysis:
    """Comprehensive trend analysis result"""

    overall_trend: str  # 'increasing', 'decreasing', 'stable', 'volatile'
    trend_strength: float  # 0-1
    trend_direction: float  # slope coefficient
    statistical_significance: float
    change_rate: float  # percentage change rate
    volatility: float
    recommendations: List[str]


class AccessTrendsAnalyzer:
    """Enhanced trends analyzer with time series analysis"""

    def __init__(
        self,
        forecast_periods: int = 30,
        confidence_level: float = 0.95,
        min_data_points: int = 14,
        logger: Optional[logging.Logger] = None,
    ):
        self.forecast_periods = forecast_periods
        self.confidence_level = confidence_level
        self.min_data_points = min_data_points
        self.logger = logger or logging.getLogger(__name__)

    def analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Main analysis method with legacy compatibility"""
        try:
            result = self.analyze_access_trends(df)
            return self._convert_to_legacy_format(result)
        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
            return self._empty_legacy_result()

    def analyze_access_trends(self, df: pd.DataFrame) -> TrendAnalysis:
        """Enhanced trend analysis method"""
        try:
            # Prepare time series data
            ts_data = self._prepare_time_series(df)

            if len(ts_data) < self.min_data_points:
                return self._insufficient_data_result()

            # Overall trend analysis
            trend_stats = self._analyze_overall_trend(ts_data)

            # Calculate volatility
            volatility = self._calculate_volatility(ts_data)

            # Generate recommendations
            recommendations = self._generate_trend_recommendations(
                trend_stats, volatility
            )

            return TrendAnalysis(
                overall_trend=trend_stats["trend_direction_label"],
                trend_strength=trend_stats["trend_strength"],
                trend_direction=trend_stats["slope"],
                statistical_significance=trend_stats["p_value"],
                change_rate=trend_stats["change_rate"],
                volatility=volatility,
                recommendations=recommendations,
            )

        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
            return self._empty_trend_analysis()

    def _prepare_time_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare time series data for analysis"""
        df_clean = df.copy(deep=False)

        # Handle Unicode issues
        from security.unicode_security_handler import UnicodeSecurityHandler

        string_columns = df_clean.select_dtypes(include=["object"]).columns
        for col in string_columns:
            df_clean[col] = df_clean[col].astype(str).apply(
                UnicodeSecurityHandler.sanitize_unicode_input
            )

        # Convert timestamp
        if not pd.api.types.is_datetime64_any_dtype(df_clean["timestamp"]):
            df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"])

        # Create time series aggregations
        df_clean["date"] = df_clean["timestamp"].dt.date

        # Daily aggregation
        daily_stats = (
            df_clean.groupby("date")
            .agg(
                {
                    "event_id": "count",
                    "person_id": "nunique",
                    "access_result": lambda x: (x == "Granted").mean(),
                }
            )
            .rename(
                columns={
                    "event_id": "total_events",
                    "person_id": "unique_users",
                    "access_result": "success_rate",
                }
            )
        )

        # Convert date index to datetime
        daily_stats.index = pd.to_datetime(daily_stats.index)
        daily_stats = daily_stats.sort_index()

        # Fill missing dates with zeros
        date_range = pd.date_range(
            start=daily_stats.index.min(), end=daily_stats.index.max(), freq="D"
        )
        daily_stats = daily_stats.reindex(date_range, fill_value=0)

        return daily_stats

    def _analyze_overall_trend(self, ts_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall trend using multiple methods"""

        y = ts_data["total_events"].to_numpy(dtype=float)
        x = np.arange(len(y))

        if len(y) > 1:
            result = stats.linregress(x, y)
            slope = float(result.slope)
            r_value = float(result.rvalue)
            p_value = float(result.pvalue)
            std_err = float(result.stderr)

            # Mann-Kendall test for monotonic trend
            mk_trend, mk_p_value = self._mann_kendall_test(y)

            # Calculate trend strength (R-squared)
            trend_strength = r_value**2

            # Calculate percentage change rate
            if len(y) >= 2:
                start_value = np.mean(y[: max(1, len(y) // 10)])
                end_value = np.mean(y[-max(1, len(y) // 10) :])
                change_rate = ((end_value - start_value) / max(start_value, 1)) * 100
            else:
                change_rate = 0

            # Determine trend direction
            if abs(slope) < std_err:
                trend_direction = "stable"
            elif slope > 0:
                trend_direction = "increasing"
            else:
                trend_direction = "decreasing"

        else:
            slope, p_value, trend_strength, change_rate = 0, 1, 0, 0
            mk_trend, mk_p_value = "no trend", 1
            trend_direction = "stable"

        return {
            "slope": slope,
            "p_value": p_value,
            "mann_kendall_trend": mk_trend,
            "mann_kendall_p_value": mk_p_value,
            "trend_strength": trend_strength,
            "change_rate": change_rate,
            "trend_direction_label": trend_direction,
        }

    def _mann_kendall_test(self, data: np.ndarray) -> Tuple[str, float]:
        """Mann-Kendall test for monotonic trend"""
        data = np.asarray(data, dtype=float)
        n = len(data)
        if n < 3:
            return "insufficient_data", 1.0

        # Calculate S statistic
        S = 0
        for i in range(n - 1):
            for j in range(i + 1, n):
                if data[j] > data[i]:
                    S += 1
                elif data[j] < data[i]:
                    S -= 1

        # Calculate variance
        var_S = n * (n - 1) * (2 * n + 5) / 18

        # Calculate Z statistic
        if S > 0:
            Z = (S - 1) / np.sqrt(var_S)
        elif S < 0:
            Z = (S + 1) / np.sqrt(var_S)
        else:
            Z = 0

        # Calculate p-value (two-tailed test)
        p_value = float(2 * (1 - stats.norm.cdf(abs(Z))))

        # Determine trend
        if p_value < 0.05:
            if S > 0:
                trend = "increasing"
            else:
                trend = "decreasing"
        else:
            trend = "no trend"

        return trend, p_value

    def _calculate_volatility(self, ts_data: pd.DataFrame) -> float:
        """Calculate volatility of the time series"""
        y = ts_data["total_events"].to_numpy(dtype=float)

        if len(y) < 2:
            return 0.0

        # Calculate coefficient of variation
        mean_val = float(np.mean(y))
        std_val = float(np.std(y))

        if mean_val == 0:
            return 0.0

        volatility = std_val / mean_val
        return min(2.0, volatility)

    def _detect_anomalous_periods(self, ts_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalous periods in the time series"""
        anomalies = []

        try:
            y = ts_data["total_events"].to_numpy(dtype=float)

            if len(y) < 7:
                return anomalies

            # Use IQR method for outlier detection
            Q1 = float(np.percentile(y, 25))
            Q3 = float(np.percentile(y, 75))
            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            # Find anomalous periods
            anomaly_indices = np.where((y < lower_bound) | (y > upper_bound))[0]

            for idx in anomaly_indices:
                date = pd.Timestamp(ts_data.index[idx])
                value = y[idx]

                anomaly_type = "spike" if value > upper_bound else "drop"
                severity = (
                    "high" if abs(value - float(np.median(y))) > 2 * IQR else "medium"
                )

                anomalies.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "type": anomaly_type,
                        "value": value,
                        "expected_range": (lower_bound, upper_bound),
                        "severity": severity,
                        "deviation": abs(value - float(np.median(y))) / max(IQR, 1),
                    }
                )

        except Exception as e:
            self.logger.warning(f"Anomaly detection failed: {e}")

        return anomalies

    def _generate_trend_recommendations(
        self, trend_stats: Dict, volatility: float
    ) -> List[str]:
        """Generate actionable recommendations based on trend analysis"""
        recommendations = []

        # Trend-based recommendations
        if trend_stats["trend_direction_label"] == "decreasing":
            recommendations.append(
                "Access volume is decreasing. Consider investigating potential issues "
                "with access systems or changes in user behavior."
            )
        elif trend_stats["trend_direction_label"] == "increasing":
            if trend_stats["trend_strength"] > 0.7:
                recommendations.append(
                    "Strong increasing trend detected. Ensure system capacity "
                    "can handle growing access demands."
                )

        # Volatility-based recommendations
        if volatility > 1.0:
            recommendations.append(
                "High volatility detected in access patterns. Consider implementing "
                "more consistent access policies or investigating irregular usage."
            )

        # Statistical significance recommendations
        if trend_stats["p_value"] < 0.05:
            recommendations.append(
                f"Statistically significant trend detected (p-value: {trend_stats['p_value']:.3f}). "
                "Monitor closely and plan accordingly."
            )

        # Mann-Kendall specific recommendations
        mk_trend = trend_stats.get("mann_kendall_trend", "no trend")
        if mk_trend != "no trend":
            recommendations.append(
                f"Mann-Kendall test confirms {mk_trend} trend. "
                "This indicates a robust directional pattern."
            )

        # Default recommendation
        if not recommendations:
            recommendations.append(
                "Continue monitoring access trends for significant changes."
            )

        return recommendations

    def _convert_to_legacy_format(self, result: TrendAnalysis) -> Dict[str, Any]:
        """Convert TrendAnalysis to legacy dictionary format"""
        return {
            "overall_trend": result.overall_trend,
            "trend_strength": result.trend_strength,
            "change_rate": result.change_rate,
            "volatility": result.volatility,
            "trend_direction": result.trend_direction,
            "statistical_significance": result.statistical_significance,
            "recommendations": result.recommendations,
            # Legacy compatibility fields
            "daily_average": (
                abs(result.trend_direction) if result.trend_direction else 0
            ),
            "peak_usage": (
                "Increasing" if result.overall_trend == "increasing" else "Stable"
            ),
            "growth_rate": result.change_rate,
            "pattern_stability": 1 - result.volatility if result.volatility <= 1 else 0,
        }

    def _insufficient_data_result(self) -> TrendAnalysis:
        """Return result for insufficient data"""
        return TrendAnalysis(
            overall_trend="insufficient_data",
            trend_strength=0.0,
            trend_direction=0.0,
            statistical_significance=1.0,
            change_rate=0.0,
            volatility=0.0,
            recommendations=[
                "Insufficient data for reliable trend analysis. Collect more data points."
            ],
        )

    def _empty_trend_analysis(self) -> TrendAnalysis:
        """Return empty result for error cases"""
        return TrendAnalysis(
            overall_trend="error",
            trend_strength=0.0,
            trend_direction=0.0,
            statistical_significance=1.0,
            change_rate=0.0,
            volatility=0.0,
            recommendations=["Unable to perform trend analysis due to data issues."],
        )

    def _empty_legacy_result(self) -> Dict[str, Any]:
        """Return empty result in legacy format"""
        return {
            "overall_trend": "error",
            "trend_strength": 0.0,
            "change_rate": 0.0,
            "volatility": 0.0,
            "trend_direction": 0.0,
            "statistical_significance": 1.0,
            "recommendations": ["Unable to perform trend analysis due to data issues."],
            "daily_average": 0,
            "peak_usage": "Unknown",
            "growth_rate": 0.0,
            "pattern_stability": 0.0,
        }


# Factory function for compatibility
def create_trends_analyzer(**kwargs) -> AccessTrendsAnalyzer:
    """Factory function to create trends analyzer"""
    return AccessTrendsAnalyzer(**kwargs)


# Alias for enhanced version
EnhancedTrendsAnalyzer = AccessTrendsAnalyzer
create_enhanced_trends_analyzer = create_trends_analyzer

# Export for compatibility
__all__ = ["AccessTrendsAnalyzer", "create_trends_analyzer", "EnhancedTrendsAnalyzer"]
