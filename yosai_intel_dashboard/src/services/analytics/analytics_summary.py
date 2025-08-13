"""Public API wrappers for analytics generation."""

from typing import Any, cast

import pandas as pd

from .generator import AnalyticsGenerator

_generator: AnalyticsGenerator = AnalyticsGenerator()


def summarize_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """Return summary statistics for the provided dataframe."""

    return cast(dict[str, Any], _generator.summarize_dataframe(df))


def create_sample_data(n_events: int = 1000) -> pd.DataFrame:
    """Generate a sample dataframe with a default size of 1000 rows."""

    return cast(pd.DataFrame, _generator.create_sample_data(n_events))


def analyze_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """Run detailed analysis on the dataframe and return metrics."""

    return cast(dict[str, Any], _generator.analyze_dataframe(df))


def generate_basic_analytics(df: pd.DataFrame) -> dict[str, Any]:
    """Return fundamental analytics for the dataframe."""

    return cast(dict[str, Any], _generator.generate_basic_analytics(df))


def generate_sample_analytics() -> dict[str, Any]:
    """Generate a sample dataframe and return its analytics."""

    return cast(dict[str, Any], _generator.generate_sample_analytics())


__all__ = [
    "summarize_dataframe",
    "create_sample_data",
    "analyze_dataframe",
    "generate_basic_analytics",
    "generate_sample_analytics",
]
