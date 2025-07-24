from __future__ import annotations

"""Built-in processing strategies for :class:`UnicodeProcessor`."""

import re
import unicodedata
from typing import Any


class BaseStrategy:
    def apply(self, text: str) -> str:
        raise NotImplementedError


_SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")
_CONTROL_RE = re.compile(r"[\x00-\x1F\x7F]")
_DANGEROUS_PREFIX_RE = re.compile(r"^[=+\-@]+")


class SurrogateRemovalStrategy(BaseStrategy):
    """Remove UTF-16 surrogate code points."""

    def apply(self, text: str) -> str:
        return _SURROGATE_RE.sub("", text)


class ControlCharacterStrategy(BaseStrategy):
    """Strip ASCII control characters."""

    def apply(self, text: str) -> str:
        cleaned = _CONTROL_RE.sub("", text)
        return _DANGEROUS_PREFIX_RE.sub("", cleaned)


class WhitespaceNormalizationStrategy(BaseStrategy):
    """Collapse repeated whitespace and normalize to NFC."""

    def apply(self, text: str) -> str:
        normalized = unicodedata.normalize("NFC", text)
        return " ".join(normalized.split())


__all__ = [
    "SurrogateRemovalStrategy",
    "ControlCharacterStrategy",
    "WhitespaceNormalizationStrategy",
]
