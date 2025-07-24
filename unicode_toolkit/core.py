from __future__ import annotations

"""Core Unicode processing utilities with pluggable strategies."""

from typing import Any, Iterable, List, Optional

from .strategies import (
    ControlCharacterStrategy,
    SurrogateRemovalStrategy,
    WhitespaceNormalizationStrategy,
)


class UnicodeProcessor:
    """Process text using a pipeline of strategies."""

    def __init__(self, strategies: Optional[Iterable] = None) -> None:
        if strategies is None:
            strategies = [
                SurrogateRemovalStrategy(),
                ControlCharacterStrategy(),
                WhitespaceNormalizationStrategy(),
            ]
        self.strategies: List = list(strategies)

    def process(self, text: Any) -> str:
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        for strat in self.strategies:
            text = strat.apply(text)
        return text

    # Convenience wrappers -------------------------------------------------
    def clean_surrogate_chars(self, text: Any) -> str:
        return SurrogateRemovalStrategy().apply(str(text))

    def sanitize_dataframe(self, df: 'pd.DataFrame') -> 'pd.DataFrame':
        from .pandas_integration import sanitize_dataframe

        return sanitize_dataframe(df, self)

    def encode_sql_query(self, query: Any) -> str:
        from .sql_safe import encode_query

        return encode_query(query, self)


__all__ = ["UnicodeProcessor"]
