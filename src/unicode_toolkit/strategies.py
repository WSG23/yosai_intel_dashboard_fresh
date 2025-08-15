"""Deprecated strategy classes kept for backward compatibility."""

from __future__ import annotations


class BaseStrategy:
    def apply(self, text: str) -> str:  # pragma: no cover - compatibility stub
        return text


class SurrogateRemovalStrategy(BaseStrategy):
    pass


class ControlCharacterStrategy(BaseStrategy):
    pass


class WhitespaceNormalizationStrategy(BaseStrategy):
    pass


__all__ = [
    "SurrogateRemovalStrategy",
    "ControlCharacterStrategy",
    "WhitespaceNormalizationStrategy",
]
