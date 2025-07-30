from __future__ import annotations

"""High level pattern analysis."""

from typing import Any, Dict

import pandas as pd

from .calculator import Calculator


class Analyzer:
    """Perform pattern analysis using :class:`Calculator`."""

    def __init__(self, calculator: Calculator | None = None) -> None:
        self.calculator = calculator or Calculator()

    def analyze(self, df: pd.DataFrame, original_rows: int) -> Dict[str, Any]:
        return self.calculator.analyze_patterns(df, original_rows)


__all__ = ["Analyzer"]
