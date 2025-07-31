"""Public API wrappers for analytics generation."""

from typing import Any, Dict

import pandas as pd

from .analytics.generator import AnalyticsGenerator

_generator = AnalyticsGenerator()


def summarize_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    return _generator.summarize_dataframe(df)


def create_sample_data(n_events: int = 1000) -> pd.DataFrame:
    return _generator.create_sample_data(n_events)


def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    return _generator.analyze_dataframe(df)


def generate_basic_analytics(df: pd.DataFrame) -> Dict[str, Any]:
    return _generator.generate_basic_analytics(df)


def generate_sample_analytics() -> Dict[str, Any]:
    return _generator.generate_sample_analytics()


__all__ = [
    "summarize_dataframe",
    "create_sample_data",
    "analyze_dataframe",
    "generate_basic_analytics",
    "generate_sample_analytics",
]
