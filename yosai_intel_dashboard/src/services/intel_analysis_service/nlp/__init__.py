from __future__ import annotations

from typing import Literal, Set

# Simple NLP utilities for sentiment and threat classification

_POSITIVE_WORDS: Set[str] = {"good", "great", "love", "happy"}
_NEGATIVE_WORDS: Set[str] = {"bad", "terrible", "hate", "angry"}
_THREAT_WORDS: Set[str] = {"attack", "bomb", "threat", "kill"}


def _tokenize(text: str) -> Set[str]:
    """Tokenize ``text`` into a set of lowercase words."""
    return {t.lower().strip('.,!?') for t in text.split()}


def classify_sentiment(text: str) -> Literal["positive", "negative", "neutral"]:
    """Classify sentiment of ``text`` using a small keyword list."""
    tokens = _tokenize(text)
    if tokens & _POSITIVE_WORDS:
        return "positive"
    if tokens & _NEGATIVE_WORDS:
        return "negative"
    return "neutral"


def detect_threat(text: str) -> bool:
    """Return ``True`` if ``text`` contains threat-related terms."""
    tokens = _tokenize(text)
    return bool(tokens & _THREAT_WORDS)
