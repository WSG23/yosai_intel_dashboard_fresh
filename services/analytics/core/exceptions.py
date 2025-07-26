from __future__ import annotations

"""Analytics domain specific exceptions."""

from core.exceptions import YosaiBaseException


class AnalyticsError(YosaiBaseException):
    """Base class for analytics errors."""


class DataLoadError(AnalyticsError):
    """Raised when data loading fails."""


class ValidationFailure(AnalyticsError):
    """Raised when validation fails."""


class TransformationError(AnalyticsError):
    """Raised when dataframe transformation fails."""


class CalculationError(AnalyticsError):
    """Raised when metric calculation fails."""


class AggregationError(AnalyticsError):
    """Raised when aggregation fails."""


class AnalysisError(AnalyticsError):
    """Raised when high level analysis fails."""


class RepositoryError(AnalyticsError):
    """Raised when repository access fails."""


class CacheError(AnalyticsError):
    """Raised when caching fails."""


class PersistenceError(AnalyticsError):
    """Raised when persistence initialization fails."""


class EventError(AnalyticsError):
    """Raised for event system errors."""


__all__ = [
    "AnalyticsError",
    "DataLoadError",
    "ValidationFailure",
    "TransformationError",
    "CalculationError",
    "AggregationError",
    "AnalysisError",
    "RepositoryError",
    "CacheError",
    "PersistenceError",
    "EventError",
]
