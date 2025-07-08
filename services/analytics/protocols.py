"""Protocols for the analytics domain."""
from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, Protocol
import pandas as pd


class AnalyticsServiceProtocol(Protocol):
    """Analytics service contract."""

    @abstractmethod
    def process(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process a DataFrame and return analytics results."""
        ...


class DataProcessorProtocol(Protocol):
    """Protocol for analytics data processing helpers."""

    @abstractmethod
    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        ...
