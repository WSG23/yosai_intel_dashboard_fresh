from __future__ import annotations

"""Aggregation helpers for analytics."""

from typing import List

import pandas as pd


class Aggregator:
    """Simple Pandas based aggregator."""

    def aggregate(
        self, df: pd.DataFrame, groupby: List[str], metrics: List[str]
    ) -> pd.DataFrame:
        if not groupby or not metrics:
            return df
        return df.groupby(groupby)[metrics].sum().reset_index()


__all__ = ["Aggregator"]
