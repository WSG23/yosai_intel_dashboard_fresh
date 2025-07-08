"""Simple analytics data processor stub."""
from __future__ import annotations

from typing import Any, Dict
import pandas as pd

from .protocols import DataProcessorProtocol


class DataProcessor(DataProcessorProtocol):
    def process_dataframe(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        return df

    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {"rows": len(df)}
