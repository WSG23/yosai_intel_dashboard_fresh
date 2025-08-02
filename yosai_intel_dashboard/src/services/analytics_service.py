"""Top-level accessors for the analytics service."""

from .analytics.analytics_service import (
    AnalyticsService,
    RiskScoreResult,
    calculate_risk_score,
    create_analytics_service,
    get_analytics_service,
)

__all__ = [
    "AnalyticsService",
    "get_analytics_service",
    "create_analytics_service",
    "RiskScoreResult",
    "calculate_risk_score",
]
