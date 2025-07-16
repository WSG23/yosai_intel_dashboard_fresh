from __future__ import annotations

"""Enhanced Unicode processing utilities with surrogate handling."""

from dataclasses import dataclass
from enum import Enum
import logging
import re
import unicodedata
from typing import Optional

from .unicode import contains_surrogates

logger = logging.getLogger(__name__)


class SurrogateHandlingStrategy(Enum):
    """Strategies for handling surrogate characters."""

    REPLACE = "replace"
    REJECT = "reject"
    STRIP = "strip"


@dataclass
class SurrogateHandlingConfig:
    """Configuration for :class:`EnhancedUnicodeProcessor`."""

    strategy: SurrogateHandlingStrategy = SurrogateHandlingStrategy.REPLACE
    replacement_char: str = "\ufffd"
    normalize_form: str = "NFC"
    log_errors: bool = True


_SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")


class EnhancedUnicodeProcessor:
    """Process text with configurable surrogate handling."""

    def __init__(self, config: Optional[SurrogateHandlingConfig] = None) -> None:
        self.config = config or SurrogateHandlingConfig()

    def process_text(self, text: str) -> str:
        if not text:
            return ""

        if contains_surrogates(text):
            if self.config.strategy is SurrogateHandlingStrategy.REJECT:
                raise UnicodeError("Surrogate characters not allowed")
            elif self.config.strategy is SurrogateHandlingStrategy.STRIP:
                text = _SURROGATE_RE.sub("", text)
            else:  # REPLACE
                text = _SURROGATE_RE.sub(self.config.replacement_char, text)

        try:
            text = unicodedata.normalize(self.config.normalize_form, text)
        except Exception as exc:  # pragma: no cover - defensive
            if self.config.log_errors:
                logger.warning("Unicode normalization failed: %s", exc)

        return text


__all__ = [
    "EnhancedUnicodeProcessor",
    "SurrogateHandlingConfig",
    "SurrogateHandlingStrategy",
]
